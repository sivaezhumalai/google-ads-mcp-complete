"""Conversion action management tools for Google Ads API (v25)."""

from typing import Any, Dict, List, Optional
import structlog

from google.ads.googleads.errors import GoogleAdsException

from .utils import micros_to_currency, run_mutate

logger = structlog.get_logger(__name__)


class ConversionTools:
    """Create and inspect conversion actions (website leads, calls, imports)."""

    def __init__(self, auth_manager, error_handler):
        self.auth_manager = auth_manager
        self.error_handler = error_handler

    async def list_conversion_actions(
        self, customer_id: str, include_removed: bool = False
    ) -> Dict[str, Any]:
        """List all conversion actions with type, category and status."""
        try:
            client = self.auth_manager.get_client(customer_id)
            ga = client.get_service("GoogleAdsService")
            q = """
                SELECT conversion_action.id, conversion_action.name,
                    conversion_action.status, conversion_action.type,
                    conversion_action.category, conversion_action.primary_for_goal,
                    conversion_action.counting_type,
                    conversion_action.value_settings.default_value,
                    conversion_action.resource_name
                FROM conversion_action
            """
            if not include_removed:
                q += " WHERE conversion_action.status != 'REMOVED'"
            out = []
            for row in ga.search(customer_id=customer_id, query=q):
                ca = row.conversion_action
                out.append({
                    "id": str(ca.id),
                    "name": ca.name,
                    "status": ca.status.name,
                    "type": ca.type_.name,
                    "category": ca.category.name,
                    "counting_type": ca.counting_type.name,
                    "primary_for_goal": ca.primary_for_goal,
                    "default_value": ca.value_settings.default_value,
                    "resource_name": ca.resource_name,
                })
            return {"success": True, "conversion_actions": out, "count": len(out)}
        except GoogleAdsException as e:
            logger.error(f"Failed to list conversion actions: {e}")
            return self.error_handler.format_error_response(e)

    async def create_conversion_action(
        self,
        customer_id: str,
        name: str,
        category: str = "LEAD",
        action_type: str = "WEBPAGE",
        status: str = "ENABLED",
        default_value: Optional[float] = None,
        always_use_default_value: bool = False,
        counting_type: str = "ONE_PER_CLICK",
        primary_for_goal: bool = True,
        validate_only: bool = False,
    ) -> Dict[str, Any]:
        """Create a conversion action for tracking leads, calls or purchases.

        action_type examples: WEBPAGE, UPLOAD_CLICKS, UPLOAD_CALLS,
            WEBSITE_CALL, CLICK_TO_CALL, PHONE_CALL_FROM_ADS (see API enums).
        category examples: LEAD, SUBMIT_LEAD_FORM, PHONE_CALL_LEAD, PURCHASE,
            SIGNUP, CONTACT, DEFAULT.
        counting_type: ONE_PER_CLICK (leads) or MANY_PER_CLICK (sales).
        """
        try:
            client = self.auth_manager.get_client(customer_id)
            svc = client.get_service("ConversionActionService")
            op = client.get_type("ConversionActionOperation")
            ca = op.create
            ca.name = name

            type_enum = client.enums.ConversionActionTypeEnum
            cat_enum = client.enums.ConversionActionCategoryEnum
            status_enum = client.enums.ConversionActionStatusEnum
            count_enum = client.enums.ConversionActionCountingTypeEnum

            ca.type_ = getattr(type_enum, action_type.upper(), type_enum.WEBPAGE)
            ca.category = getattr(cat_enum, category.upper(), cat_enum.DEFAULT)
            ca.status = getattr(status_enum, status.upper(), status_enum.ENABLED)
            ca.counting_type = getattr(count_enum, counting_type.upper(), count_enum.ONE_PER_CLICK)
            ca.primary_for_goal = primary_for_goal

            if default_value is not None:
                ca.value_settings.default_value = float(default_value)
                ca.value_settings.always_use_default_value = always_use_default_value

            resp = run_mutate(
                client, svc.mutate_conversion_actions, "MutateConversionActionsRequest",
                customer_id, [op], validate_only=validate_only,
            )
            rn = resp.results[0].resource_name if resp.results else None
            return {
                "success": True,
                "name": name,
                "type": action_type.upper(),
                "category": category.upper(),
                "resource_name": rn,
                "validate_only": validate_only,
                "message": (f"[VALIDATE ONLY] Conversion action '{name}' is valid (not created)"
                            if validate_only else f"Conversion action '{name}' created"),
            }
        except GoogleAdsException as e:
            logger.error(f"Failed to create conversion action: {e}")
            return self.error_handler.format_error_response(e)
