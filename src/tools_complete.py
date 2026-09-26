"""Complete tools implementation combining all modules."""

import asyncio
from typing import Any, Dict, List, Optional
from datetime import datetime, timedelta
import base64
import structlog

from mcp.types import Tool
from google.ads.googleads.errors import GoogleAdsException

from .auth import GoogleAdsAuthManager
from .error_handler import ErrorHandler
from .tools_campaigns import CampaignTools
from .tools_reporting import ReportingTools
from .tools_ad_groups import AdGroupTools
from .tools_ads import AdTools
from .tools_keywords import KeywordTools
from .tools_budgets import BudgetTools
from .tools_assets import AssetTools
from .tools_extensions import ExtensionTools
from .tools_audiences import AudienceTools
from .tools_geography import GeographyTools
from .tools_bidding import BiddingTools
from .tools_conversions import ConversionTools
from .utils import currency_to_micros, micros_to_currency

logger = structlog.get_logger(__name__)


class GoogleAdsTools:
    """Complete implementation of all Google Ads API v20 tools."""
    
    def __init__(self, auth_manager: GoogleAdsAuthManager, error_handler: ErrorHandler):
        self.auth_manager = auth_manager
        self.error_handler = error_handler
        
        # Initialize tool modules
        self.campaign_tools = CampaignTools(auth_manager, error_handler)
        self.reporting_tools = ReportingTools(auth_manager, error_handler)
        self.ad_group_tools = AdGroupTools(auth_manager, error_handler)
        self.ad_tools = AdTools(auth_manager, error_handler)
        self.keyword_tools = KeywordTools(auth_manager, error_handler)
        self.budget_tools = BudgetTools(auth_manager, error_handler)
        self.asset_tools = AssetTools(auth_manager, error_handler)
        self.extension_tools = ExtensionTools(auth_manager, error_handler)
        self.audience_tools = AudienceTools(auth_manager, error_handler)
        self.geography_tools = GeographyTools(auth_manager, error_handler)
        self.bidding_tools = BiddingTools(auth_manager, error_handler)
        self.conversion_tools = ConversionTools(auth_manager, error_handler)

        self._tools_registry = self._register_all_tools()
        
    def _register_all_tools(self) -> Dict[str, Dict[str, Any]]:
        """Register all available tools from all modules."""
        tools = {}
        
        # Account Management
        tools.update(self._register_account_tools())
        
        # Campaign Management (from CampaignTools)
        tools.update(self._register_campaign_tools())
        
        # Reporting & Analytics (from ReportingTools)
        tools.update(self._register_reporting_tools())
        
        # Additional tool categories
        # Ad Group Management
        tools.update(self._register_ad_group_tools())
        
        # Ad Management
        tools.update(self._register_ad_tools())
        
        # Asset Management
        tools.update(self._register_asset_tools())
        
        # Budget Management
        tools.update(self._register_budget_tools())
        
        # Keyword Management
        tools.update(self._register_keyword_tools())
        
        # Extension Management
        tools.update(self._register_extension_tools())
        
        # Search Terms & Negative Keyword Intelligence
        tools.update(self._register_search_intelligence_tools())
        
        # Audience Management & Targeting
        tools.update(self._register_audience_tools())
        
        # Geographic Performance & Targeting
        tools.update(self._register_geography_tools())
        
        # Bidding Strategy & Bid Adjustments
        tools.update(self._register_bidding_tools())

        # Conversion action management
        tools.update(self._register_conversion_tools())

        # Raw GAQL access (read anything) + advanced features
        tools.update(self._register_raw_tools())
        tools.update(self._register_advanced_tools())

        return tools
        
    def _register_account_tools(self) -> Dict[str, Dict[str, Any]]:
        """Register account management tools."""
        return {
            "list_accounts": {
                "description": "List all accessible Google Ads accounts",
                "handler": self.list_accounts,
                "parameters": {},
            },
            "get_account_info": {
                "description": "Get detailed information about a specific account",
                "handler": self.get_account_info,
                "parameters": {
                    "customer_id": {"type": "string", "required": True},
                },
            },
            "get_account_hierarchy": {
                "description": "Get the account hierarchy tree",
                "handler": self.get_account_hierarchy,
                "parameters": {
                    "customer_id": {"type": "string", "required": True},
                },
            },
        }
        
    def _register_campaign_tools(self) -> Dict[str, Dict[str, Any]]:
        """Register campaign management tools."""
        return {
            "create_campaign": {
                "description": "Create a new campaign with budget and settings",
                "handler": self.campaign_tools.create_campaign,
                "parameters": {
                    "customer_id": {"type": "string", "required": True},
                    "name": {"type": "string", "required": True},
                    "budget_amount": {"type": "number", "required": True},
                    "campaign_type": {"type": "string", "default": "SEARCH"},
                    "bidding_strategy": {"type": "string", "default": "MAXIMIZE_CLICKS"},
                    "start_date": {"type": "string"},
                    "end_date": {"type": "string"},
                    "target_locations": {"type": "array"},
                    "target_languages": {"type": "array"},
                },
            },
            "update_campaign": {
                "description": "Update campaign settings including assigning portfolio bidding strategies",
                "handler": self.campaign_tools.update_campaign,
                "parameters": {
                    "customer_id": {"type": "string", "required": True},
                    "campaign_id": {"type": "string", "required": True},
                    "name": {"type": "string"},
                    "status": {"type": "string"},
                    "start_date": {"type": "string"},
                    "end_date": {"type": "string"},
                    "bidding_strategy": {"type": "string"},
                    "validate_only": {"type": "boolean", "default": False},
                },
            },
            "pause_campaign": {
                "description": "Pause a running campaign",
                "handler": self.campaign_tools.pause_campaign,
                "parameters": {
                    "customer_id": {"type": "string", "required": True},
                    "campaign_id": {"type": "string", "required": True},
                },
            },
            "resume_campaign": {
                "description": "Resume a paused campaign",
                "handler": self.campaign_tools.resume_campaign,
                "parameters": {
                    "customer_id": {"type": "string", "required": True},
                    "campaign_id": {"type": "string", "required": True},
                },
            },
            "list_campaigns": {
                "description": "List all campaigns with optional filters",
                "handler": self.campaign_tools.list_campaigns,
                "parameters": {
                    "customer_id": {"type": "string", "required": True},
                    "status": {"type": "string"},
                    "campaign_type": {"type": "string"},
                },
            },
            "get_campaign": {
                "description": "Get detailed campaign information",
                "handler": self.campaign_tools.get_campaign,
                "parameters": {
                    "customer_id": {"type": "string", "required": True},
                    "campaign_id": {"type": "string", "required": True},
                },
            },
            "delete_campaign": {
                "description": "Delete (REMOVE) a campaign. Supports validate_only dry-run.",
                "handler": self.campaign_tools.delete_campaign,
                "parameters": {
                    "customer_id": {"type": "string", "required": True},
                    "campaign_id": {"type": "string", "required": True},
                    "validate_only": {"type": "boolean", "default": False},
                },
            },
            "copy_campaign": {
                "description": "Copy an existing campaign with a new name and budget",
                "handler": self.campaign_tools.copy_campaign,
                "parameters": {
                    "customer_id": {"type": "string", "required": True},
                    "source_campaign_id": {"type": "string", "required": True},
                    "new_name": {"type": "string", "required": True},
                    "budget_amount": {"type": "number"},
                },
            },
            "create_ad_schedule": {
                "description": "Create ad schedules (dayparting) for a campaign with specific days, hours, and bid adjustments",
                "handler": self.campaign_tools.create_ad_schedule,
                "parameters": {
                    "customer_id": {"type": "string", "required": True},
                    "campaign_id": {"type": "string", "required": True},
                    "schedules": {"type": "array", "required": True},
                },
            },
            "get_campaign_overview": {
                "description": "Get comprehensive high-level campaign overview showing keywords, extensions, scheduling, audiences, performance, and optimization score",
                "handler": self.campaign_tools.get_campaign_overview,
                "parameters": {
                    "customer_id": {"type": "string", "required": True},
                    "campaign_id": {"type": "string", "required": True},
                    "date_range": {"type": "string", "default": "LAST_30_DAYS"},
                },
            },
            "set_campaign_bidding_strategy": {
                "description": "Switch a campaign to a STANDARD bidding strategy: MAXIMIZE_CLICKS, MAXIMIZE_CONVERSIONS, TARGET_CPA, MAXIMIZE_CONVERSION_VALUE, TARGET_ROAS, MANUAL_CPC, or TARGET_IMPRESSION_SHARE. Optional: cpc_bid_ceiling_micros, target_cpa_micros, target_roas, impression-share params. Supports validate_only.",
                "handler": self.campaign_tools.set_campaign_bidding_strategy,
                "parameters": {
                    "customer_id": {"type": "string", "required": True},
                    "campaign_id": {"type": "string", "required": True},
                    "strategy_type": {"type": "string", "required": True},
                    "cpc_bid_ceiling_micros": {"type": "number"},
                    "target_cpa_micros": {"type": "number"},
                    "target_roas": {"type": "number"},
                    "target_impression_share_location": {"type": "string", "default": "ANYWHERE_ON_PAGE"},
                    "target_impression_share_fraction_micros": {"type": "number"},
                    "enhanced_cpc": {"type": "boolean", "default": False},
                    "validate_only": {"type": "boolean", "default": False},
                },
            },
            "add_campaign_location": {
                "description": "Add or exclude geo targeting on a campaign. locations = place names ('Jigani','Bengaluru'), numeric geo IDs, or geoTargetConstants/<id> resource names. Set negative=true to exclude. Supports validate_only.",
                "handler": self.campaign_tools.add_campaign_location,
                "parameters": {
                    "customer_id": {"type": "string", "required": True},
                    "campaign_id": {"type": "string", "required": True},
                    "locations": {"type": "array", "required": True},
                    "country_code": {"type": "string", "default": "IN"},
                    "negative": {"type": "boolean", "default": False},
                    "validate_only": {"type": "boolean", "default": False},
                },
            },
            "set_eu_political_advertising": {
                "description": "Declare whether a campaign contains EU political advertising. Required by Google before some edits (e.g. location targeting). Non-political/non-EU advertisers set contains_eu_political_ads=false. Supports validate_only.",
                "handler": self.campaign_tools.set_eu_political_advertising,
                "parameters": {
                    "customer_id": {"type": "string", "required": True},
                    "campaign_id": {"type": "string", "required": True},
                    "contains_eu_political_ads": {"type": "boolean", "default": False},
                    "validate_only": {"type": "boolean", "default": False},
                },
            },
            "add_campaign_language": {
                "description": "Add language targeting to a campaign. languages = names (English, Hindi, Kannada, Tamil, Telugu, ...) or numeric language constant IDs. Supports validate_only.",
                "handler": self.campaign_tools.add_campaign_language,
                "parameters": {
                    "customer_id": {"type": "string", "required": True},
                    "campaign_id": {"type": "string", "required": True},
                    "languages": {"type": "array", "required": True},
                    "validate_only": {"type": "boolean", "default": False},
                },
            },
            "list_campaign_criteria": {
                "description": "List a campaign's criteria (locations, languages, campaign-level negative keywords, proximity) with resource names and criterion IDs for use with remove_campaign_criterion.",
                "handler": self.campaign_tools.list_campaign_criteria,
                "parameters": {
                    "customer_id": {"type": "string", "required": True},
                    "campaign_id": {"type": "string", "required": True},
                    "criterion_type": {"type": "string"},
                },
            },
            "remove_campaign_criterion": {
                "description": "Remove a campaign criterion (targeted/excluded location, language, or campaign-level negative keyword). Provide criterion_resource_name OR campaign_id + criterion_id. Supports validate_only.",
                "handler": self.campaign_tools.remove_campaign_criterion,
                "parameters": {
                    "customer_id": {"type": "string", "required": True},
                    "criterion_resource_name": {"type": "string"},
                    "campaign_id": {"type": "string"},
                    "criterion_id": {"type": "string"},
                    "validate_only": {"type": "boolean", "default": False},
                },
            },
        }

    def _register_ad_group_tools(self) -> Dict[str, Dict[str, Any]]:
        """Register ad group management tools."""
        return {
            "create_ad_group": {
                "description": "Create a new ad group in a campaign",
                "handler": self.ad_group_tools.create_ad_group,
                "parameters": {
                    "customer_id": {"type": "string", "required": True},
                    "campaign_id": {"type": "string", "required": True},
                    "name": {"type": "string", "required": True},
                    "cpc_bid_micros": {"type": "number"},
                },
            },
            "update_ad_group": {
                "description": "Update ad group settings",
                "handler": self.ad_group_tools.update_ad_group,
                "parameters": {
                    "customer_id": {"type": "string", "required": True},
                    "ad_group_id": {"type": "string", "required": True},
                    "name": {"type": "string"},
                    "status": {"type": "string"},
                    "cpc_bid_micros": {"type": "number"},
                },
            },
            "list_ad_groups": {
                "description": "List ad groups with filters",
                "handler": self.ad_group_tools.list_ad_groups,
                "parameters": {
                    "customer_id": {"type": "string", "required": True},
                    "campaign_id": {"type": "string"},
                    "status": {"type": "string"},
                },
            },
        }
        
    def _register_ad_tools(self) -> Dict[str, Dict[str, Any]]:
        """Register ad management tools."""
        return {
            "create_responsive_search_ad": {
                "description": "Create a responsive search ad",
                "handler": self.ad_tools.create_responsive_search_ad,
                "parameters": {
                    "customer_id": {"type": "string", "required": True},
                    "ad_group_id": {"type": "string", "required": True},
                    "headlines": {"type": "array", "required": True},
                    "descriptions": {"type": "array", "required": True},
                    "final_urls": {"type": "array", "required": True},
                    "path1": {"type": "string"},
                    "path2": {"type": "string"},
                },
            },
            "create_expanded_text_ad": {
                "description": "Create an expanded text ad",
                "handler": self.ad_tools.create_expanded_text_ad,
                "parameters": {
                    "customer_id": {"type": "string", "required": True},
                    "ad_group_id": {"type": "string", "required": True},
                    "headline1": {"type": "string", "required": True},
                    "headline2": {"type": "string", "required": True},
                    "headline3": {"type": "string"},
                    "description1": {"type": "string", "required": True},
                    "description2": {"type": "string"},
                    "final_urls": {"type": "array", "required": True},
                },
            },
            "list_ads": {
                "description": "List ads with filters",
                "handler": self.ad_tools.list_ads,
                "parameters": {
                    "customer_id": {"type": "string", "required": True},
                    "ad_group_id": {"type": "string"},
                    "campaign_id": {"type": "string"},
                    "status": {"type": "string"},
                },
            },
            "update_ad": {
                "description": "Update an existing ad",
                "handler": self.ad_tools.update_ad,
                "parameters": {
                    "customer_id": {"type": "string", "required": True},
                    "ad_group_id": {"type": "string", "required": True},
                    "ad_id": {"type": "string", "required": True},
                    "headlines": {"type": "array"},
                    "descriptions": {"type": "array"},
                    "final_urls": {"type": "array"},
                    "status": {"type": "string"},
                },
            },
            "pause_ad": {
                "description": "Pause a specific ad",
                "handler": self.ad_tools.pause_ad,
                "parameters": {
                    "customer_id": {"type": "string", "required": True},
                    "ad_group_id": {"type": "string", "required": True},
                    "ad_id": {"type": "string", "required": True},
                },
            },
            "enable_ad": {
                "description": "Enable a specific ad",
                "handler": self.ad_tools.enable_ad,
                "parameters": {
                    "customer_id": {"type": "string", "required": True},
                    "ad_group_id": {"type": "string", "required": True},
                    "ad_id": {"type": "string", "required": True},
                },
            },
            "delete_ad": {
                "description": "Delete (REMOVE) a specific ad. Supports validate_only dry-run.",
                "handler": self.ad_tools.delete_ad,
                "parameters": {
                    "customer_id": {"type": "string", "required": True},
                    "ad_group_id": {"type": "string", "required": True},
                    "ad_id": {"type": "string", "required": True},
                    "validate_only": {"type": "boolean", "default": False},
                },
            },
            "compare_ad_performance": {
                "description": "Compare performance of multiple ads side-by-side with efficiency analysis",
                "handler": self.ad_tools.compare_ad_performance,
                "parameters": {
                    "customer_id": {"type": "string", "required": True},
                    "ad_ids": {"type": "array", "required": True},
                    "ad_group_id": {"type": "string", "required": True},
                    "date_range": {"type": "string", "default": "LAST_30_DAYS"},
                },
            },
            "get_ad_group_performance_ranking": {
                "description": "Rank all ads in an ad group by performance metrics (CTR, ROAS, efficiency)",
                "handler": self.ad_tools.get_ad_group_performance_ranking,
                "parameters": {
                    "customer_id": {"type": "string", "required": True},
                    "ad_group_id": {"type": "string", "required": True},
                    "date_range": {"type": "string", "default": "LAST_30_DAYS"},
                    "sort_by": {"type": "string", "default": "efficiency_score"},
                },
            },
            "identify_optimization_opportunities": {
                "description": "Auto-identify which ads to pause, optimize, or scale based on performance",
                "handler": self.ad_tools.identify_optimization_opportunities,
                "parameters": {
                    "customer_id": {"type": "string", "required": True},
                    "ad_group_id": {"type": "string"},
                    "campaign_id": {"type": "string"},
                    "date_range": {"type": "string", "default": "LAST_30_DAYS"},
                    "min_clicks": {"type": "number", "default": 10},
                },
            },
            "calculate_roas_by_ad": {
                "description": "Calculate Return on Ad Spend (ROAS) for each ad with profitability analysis",
                "handler": self.ad_tools.calculate_roas_by_ad,
                "parameters": {
                    "customer_id": {"type": "string", "required": True},
                    "ad_group_id": {"type": "string"},
                    "campaign_id": {"type": "string"},
                    "date_range": {"type": "string", "default": "LAST_30_DAYS"},
                    "min_cost": {"type": "number", "default": 5.0},
                },
            },
            "analyze_ad_strength_trends": {
                "description": "Analyze how ad strength ratings correlate with performance trends over time",
                "handler": self.ad_tools.analyze_ad_strength_trends,
                "parameters": {
                    "customer_id": {"type": "string", "required": True},
                    "ad_group_id": {"type": "string", "required": True},
                    "current_date_range": {"type": "string", "default": "LAST_7_DAYS"},
                    "comparison_date_range": {"type": "string", "default": "LAST_30_DAYS"},
                },
            },
        }
        
    def _register_asset_tools(self) -> Dict[str, Dict[str, Any]]:
        """Register asset management tools."""
        return {
            "upload_image_asset": {
                "description": "Upload an image asset",
                "handler": self.asset_tools.upload_image_asset,
                "parameters": {
                    "customer_id": {"type": "string", "required": True},
                    "image_data": {"type": "string", "required": True},
                    "name": {"type": "string", "required": True},
                },
            },
            "upload_text_asset": {
                "description": "Create a text asset",
                "handler": self.asset_tools.upload_text_asset,
                "parameters": {
                    "customer_id": {"type": "string", "required": True},
                    "text": {"type": "string", "required": True},
                    "name": {"type": "string", "required": True},
                },
            },
            "list_assets": {
                "description": "List all assets",
                "handler": self.asset_tools.list_assets,
                "parameters": {
                    "customer_id": {"type": "string", "required": True},
                    "asset_type": {"type": "string"},
                },
            },
        }
        
    def _register_budget_tools(self) -> Dict[str, Dict[str, Any]]:
        """Register budget management tools."""
        return {
            "create_budget": {
                "description": "Create a shared campaign budget",
                "handler": self.budget_tools.create_budget,
                "parameters": {
                    "customer_id": {"type": "string", "required": True},
                    "name": {"type": "string", "required": True},
                    "amount_micros": {"type": "number", "required": True},
                    "delivery_method": {"type": "string", "default": "STANDARD"},
                },
            },
            "update_budget": {
                "description": "Update budget amount or settings",
                "handler": self.budget_tools.update_budget,
                "parameters": {
                    "customer_id": {"type": "string", "required": True},
                    "budget_id": {"type": "string", "required": True},
                    "amount_micros": {"type": "number"},
                    "name": {"type": "string"},
                },
            },
            "list_budgets": {
                "description": "List all budgets",
                "handler": self.budget_tools.list_budgets,
                "parameters": {
                    "customer_id": {"type": "string", "required": True},
                },
            },
        }
        
    def _register_keyword_tools(self) -> Dict[str, Dict[str, Any]]:
        """Register keyword management tools."""
        return {
            "add_keywords": {
                "description": "Add keywords to an ad group",
                "handler": self.keyword_tools.add_keywords,
                "parameters": {
                    "customer_id": {"type": "string", "required": True},
                    "ad_group_id": {"type": "string", "required": True},
                    "keywords": {"type": "array", "required": True},
                },
            },
            "add_negative_keywords": {
                "description": "Add negative keywords (campaign or ad group level). SYNTAX: keywords=['free','cheap','demo'] as array of strings. Use EITHER campaign_id OR ad_group_id, not both. Tool automatically creates KeywordInfo protobuf objects.",
                "handler": self.keyword_tools.add_negative_keywords,
                "parameters": {
                    "customer_id": {"type": "string", "required": True},
                    "keywords": {"type": "array", "required": True, "description": "Array of negative keyword strings, e.g. ['free', 'cheap', 'demo']"},
                    "campaign_id": {"type": "string", "description": "For campaign-level negative keywords"},
                    "ad_group_id": {"type": "string", "description": "For ad group-level negative keywords"},
                },
            },
            "list_keywords": {
                "description": "List keywords with performance data",
                "handler": self.keyword_tools.list_keywords,
                "parameters": {
                    "customer_id": {"type": "string", "required": True},
                    "ad_group_id": {"type": "string"},
                    "campaign_id": {"type": "string"},
                },
            },
            "update_keyword_bid": {
                "description": "Update the CPC bid for a specific keyword",
                "handler": self.keyword_tools.update_keyword_bid,
                "parameters": {
                    "customer_id": {"type": "string", "required": True},
                    "ad_group_id": {"type": "string", "required": True},
                    "keyword_id": {"type": "string", "required": True},
                    "cpc_bid_micros": {"type": "number", "required": True},
                },
            },
            "delete_keyword": {
                "description": "Delete (REMOVE) a specific keyword. Supports validate_only dry-run.",
                "handler": self.keyword_tools.delete_keyword,
                "parameters": {
                    "customer_id": {"type": "string", "required": True},
                    "ad_group_id": {"type": "string", "required": True},
                    "keyword_id": {"type": "string", "required": True},
                    "validate_only": {"type": "boolean", "default": False},
                },
            },
            "pause_keyword": {
                "description": "Pause a specific keyword",
                "handler": self.keyword_tools.pause_keyword,
                "parameters": {
                    "customer_id": {"type": "string", "required": True},
                    "ad_group_id": {"type": "string", "required": True},
                    "keyword_id": {"type": "string", "required": True},
                },
            },
            "enable_keyword": {
                "description": "Enable a paused keyword",
                "handler": self.keyword_tools.enable_keyword,
                "parameters": {
                    "customer_id": {"type": "string", "required": True},
                    "ad_group_id": {"type": "string", "required": True},
                    "keyword_id": {"type": "string", "required": True},
                },
            },
            "get_keyword_performance": {
                "description": "Get keyword performance data with quality scores",
                "handler": self.keyword_tools.get_keyword_performance,
                "parameters": {
                    "customer_id": {"type": "string", "required": True},
                    "ad_group_id": {"type": "string"},
                    "date_range": {"type": "string", "default": "LAST_30_DAYS"},
                },
            },
        }
        
    def _register_extension_tools(self) -> Dict[str, Dict[str, Any]]:
        """Register extension management tools."""
        return {
            "create_sitelink_extensions": {
                "description": "Create sitelink extensions for a campaign. SYNTAX: sitelinks=[{'text':'Features','url':'https://site.com/features','description1':'Optional desc'}]",
                "handler": self.extension_tools.create_sitelink_extensions,
                "parameters": {
                    "customer_id": {"type": "string", "required": True},
                    "campaign_id": {"type": "string", "required": True},
                    "sitelinks": {"type": "array", "required": True, "description": "Array of objects with 'text', 'url', optional 'description1', 'description2'"},
                },
            },
            "create_callout_extensions": {
                "description": "Create callout extensions for a campaign",
                "handler": self.extension_tools.create_callout_extensions,
                "parameters": {
                    "customer_id": {"type": "string", "required": True},
                    "campaign_id": {"type": "string", "required": True},
                    "callouts": {"type": "array", "required": True},
                },
            },
            "create_structured_snippet_extensions": {
                "description": "Create structured snippet extensions for a campaign. SYNTAX: structured_snippets=[{'header':'SERVICE_CATALOG','values':['Web Design','SEO']}]. Valid headers: AMENITIES, BRANDS, COURSES, DESTINATIONS, MODELS, SERVICE_CATALOG, SERVICES, FEATURES (maps to SERVICE_CATALOG), STYLES, TYPES.",
                "handler": self.extension_tools.create_structured_snippet_extensions,
                "parameters": {
                    "customer_id": {"type": "string", "required": True},
                    "campaign_id": {"type": "string", "required": True},
                    "structured_snippets": {"type": "array", "required": True, "description": "Array of objects with 'header' (predefined Google value) and 'values' (array of strings)"},
                },
            },
            "create_call_extensions": {
                "description": "Create call extensions for a campaign",
                "handler": self.extension_tools.create_call_extensions,
                "parameters": {
                    "customer_id": {"type": "string", "required": True},
                    "campaign_id": {"type": "string", "required": True},
                    "phone_number": {"type": "string", "required": True},
                    "country_code": {"type": "string", "default": "US"},
                    "call_only": {"type": "boolean", "default": False},
                },
            },
            "list_extensions": {
                "description": "List extensions for a campaign or account",
                "handler": self.extension_tools.list_extensions,
                "parameters": {
                    "customer_id": {"type": "string", "required": True},
                    "campaign_id": {"type": "string"},
                    "extension_type": {"type": "string"},
                },
            },
            "delete_extension": {
                "description": "Delete a specific extension",
                "handler": self.extension_tools.delete_extension,
                "parameters": {
                    "customer_id": {"type": "string", "required": True},
                    "extension_id": {"type": "string", "required": True},
                },
            },
        }
        
    def _register_reporting_tools(self) -> Dict[str, Dict[str, Any]]:
        """Register reporting and analytics tools."""
        return {
            "get_campaign_performance": {
                "description": "Get campaign performance metrics",
                "handler": self.reporting_tools.get_campaign_performance,
                "parameters": {
                    "customer_id": {"type": "string", "required": True},
                    "campaign_id": {"type": "string"},
                    "date_range": {"type": "string", "default": "LAST_30_DAYS"},
                    "metrics": {"type": "array"},
                },
            },
            "get_ad_group_performance": {
                "description": "Get ad group performance metrics",
                "handler": self.reporting_tools.get_ad_group_performance,
                "parameters": {
                    "customer_id": {"type": "string", "required": True},
                    "ad_group_id": {"type": "string"},
                    "date_range": {"type": "string", "default": "LAST_30_DAYS"},
                },
            },
            "get_keyword_performance": {
                "description": "Get keyword performance metrics",
                "handler": self.reporting_tools.get_keyword_performance,
                "parameters": {
                    "customer_id": {"type": "string", "required": True},
                    "ad_group_id": {"type": "string"},
                    "date_range": {"type": "string", "default": "LAST_30_DAYS"},
                },
            },
            # "run_gaql_query": {
            #     "description": "Run custom GAQL queries",
            #     "handler": self.reporting_tools.run_gaql_query,
            #     "parameters": {
            #         "customer_id": {"type": "string", "required": True},
            #         "query": {"type": "string", "required": True},
            #     },
            # },
            "get_search_terms_report": {
                "description": "Get search terms report",
                "handler": self.reporting_tools.get_search_terms_report,
                "parameters": {
                    "customer_id": {"type": "string", "required": True},
                    "campaign_id": {"type": "string"},
                    "ad_group_id": {"type": "string"},
                    "date_range": {"type": "string", "default": "LAST_7_DAYS"},
                },
            },
        }
        
    def _register_advanced_tools(self) -> Dict[str, Dict[str, Any]]:
        """Register advanced feature tools."""
        return {
            "get_recommendations": {
                "description": "Get Google Ads optimization recommendations (keyword ideas, budget, bidding, ad strength, etc.). Optional recommendation_type filter (e.g. KEYWORD, CAMPAIGN_BUDGET, TARGET_CPA_OPT_IN).",
                "handler": self.get_recommendations,
                "parameters": {
                    "customer_id": {"type": "string", "required": True},
                    "recommendation_type": {"type": "string"},
                    "limit": {"type": "number", "default": 50},
                },
            },
            "apply_recommendation": {
                "description": "Apply a specific recommendation by its resource name (from get_recommendations). Supports validate_only.",
                "handler": self.apply_recommendation,
                "parameters": {
                    "customer_id": {"type": "string", "required": True},
                    "recommendation_resource_name": {"type": "string", "required": True},
                    "validate_only": {"type": "boolean", "default": False},
                },
            },
            "dismiss_recommendation": {
                "description": "Dismiss (hide) a recommendation by its resource name.",
                "handler": self.dismiss_recommendation,
                "parameters": {
                    "customer_id": {"type": "string", "required": True},
                    "recommendation_resource_name": {"type": "string", "required": True},
                },
            },
            "get_change_history": {
                "description": "Get account change history (who changed what, when) from the change_event resource. days_ago must be 1-29 (API limit).",
                "handler": self.get_change_history,
                "parameters": {
                    "customer_id": {"type": "string", "required": True},
                    "days_ago": {"type": "number", "default": 14},
                    "limit": {"type": "number", "default": 200},
                },
            },
        }

    def _register_conversion_tools(self) -> Dict[str, Dict[str, Any]]:
        """Register conversion action tools."""
        return {
            "list_conversion_actions": {
                "description": "List all conversion actions (name, type, category, status, primary/secondary) — e.g. Website lead, Calls from ads.",
                "handler": self.conversion_tools.list_conversion_actions,
                "parameters": {
                    "customer_id": {"type": "string", "required": True},
                    "include_removed": {"type": "boolean", "default": False},
                },
            },
            "create_conversion_action": {
                "description": "Create a conversion action for tracking leads/calls/purchases. category: LEAD, SUBMIT_LEAD_FORM, PHONE_CALL_LEAD, PURCHASE, CONTACT, DEFAULT. action_type: WEBPAGE, CLICK_TO_CALL, WEBSITE_CALL, UPLOAD_CLICKS, UPLOAD_CALLS. Supports validate_only.",
                "handler": self.conversion_tools.create_conversion_action,
                "parameters": {
                    "customer_id": {"type": "string", "required": True},
                    "name": {"type": "string", "required": True},
                    "category": {"type": "string", "default": "LEAD"},
                    "action_type": {"type": "string", "default": "WEBPAGE"},
                    "status": {"type": "string", "default": "ENABLED"},
                    "default_value": {"type": "number"},
                    "always_use_default_value": {"type": "boolean", "default": False},
                    "counting_type": {"type": "string", "default": "ONE_PER_CLICK"},
                    "primary_for_goal": {"type": "boolean", "default": True},
                    "validate_only": {"type": "boolean", "default": False},
                },
            },
        }

    def _register_raw_tools(self) -> Dict[str, Dict[str, Any]]:
        """Register raw GAQL access tools (read anything in the account)."""
        return {
            "run_gaql_query": {
                "description": "Run any read-only GAQL (Google Ads Query Language) query and return rows. Use this to read ANY resource/field not covered by a specific tool. Example: SELECT campaign.name, metrics.clicks FROM campaign WHERE segments.date DURING LAST_7_DAYS.",
                "handler": self.reporting_tools.run_gaql_query,
                "parameters": {
                    "customer_id": {"type": "string", "required": True},
                    "query": {"type": "string", "required": True},
                    "limit": {"type": "number", "default": 1000},
                },
            },
            "search_geo_targets": {
                "description": "Resolve place names to geo target IDs (for location targeting). names = ['Jigani','Anekal']; returns geoTargetConstants/<id>, canonical name and type.",
                "handler": self.search_geo_targets,
                "parameters": {
                    "customer_id": {"type": "string", "required": True},
                    "names": {"type": "array", "required": True},
                    "country_code": {"type": "string", "default": "IN"},
                    "locale": {"type": "string", "default": "en"},
                },
            },
        }

    def get_all_tools(self) -> List[Tool]:
        """Get all tools in MCP format."""
        tools = []
        for name, config in self._tools_registry.items():
            # Extract required parameters
            required_params = []
            properties = {}
            
            for param_name, param_config in config["parameters"].items():
                # Create property schema without the 'required' field
                prop_schema = {k: v for k, v in param_config.items() if k != "required"}
                properties[param_name] = prop_schema
                
                # Add to required list if marked as required
                if param_config.get("required", False):
                    required_params.append(param_name)
            
            tool = Tool(
                name=name,
                description=config["description"],
                inputSchema={
                    "type": "object",
                    "properties": properties,
                    "required": required_params,
                },
            )
            tools.append(tool)
        return tools
        
    async def execute_tool(self, name: str, arguments: Dict[str, Any]) -> Any:
        """Execute a tool by name."""
        if name not in self._tools_registry:
            raise ValueError(f"Unknown tool: {name}")
            
        tool_config = self._tools_registry[name]
        handler = tool_config["handler"]
        
        # Validate required parameters
        for param, config in tool_config["parameters"].items():
            if config.get("required", False) and param not in arguments:
                raise ValueError(f"Missing required parameter: {param}")
                
        # Execute the handler
        return await handler(**arguments)
        
    # Account Management Methods
    
    async def list_accounts(self) -> Dict[str, Any]:
        """List all accessible Google Ads accounts."""
        try:
            customers = self.auth_manager.get_accessible_customers()
            return {
                "success": True,
                "accounts": customers,
                "count": len(customers),
            }
        except Exception as e:
            logger.error(f"Failed to list accounts: {e}")
            raise
            
    async def get_account_info(self, customer_id: str) -> Dict[str, Any]:
        """Get detailed account information."""
        try:
            client = self.auth_manager.get_client(customer_id)
            googleads_service = client.get_service("GoogleAdsService")
            
            query = """
                SELECT
                    customer.id,
                    customer.descriptive_name,
                    customer.currency_code,
                    customer.time_zone,
                    customer.auto_tagging_enabled,
                    customer.manager,
                    customer.test_account,
                    customer.optimization_score,
                    customer.optimization_score_weight
                FROM customer
                LIMIT 1
            """
            
            response = googleads_service.search(
                customer_id=customer_id,
                query=query,
            )
            
            for row in response:
                return {
                    "success": True,
                    "account": {
                        "id": str(row.customer.id),
                        "name": row.customer.descriptive_name,
                        "currency_code": row.customer.currency_code,
                        "time_zone": row.customer.time_zone,
                        "auto_tagging_enabled": row.customer.auto_tagging_enabled,
                        "is_manager": row.customer.manager,
                        "is_test_account": row.customer.test_account,
                        "optimization_score": row.customer.optimization_score,
                        "optimization_score_weight": row.customer.optimization_score_weight,
                    },
                }
                
            return {"success": False, "error": "Account not found"}
            
        except Exception as e:
            logger.error(f"Failed to get account info: {e}")
            raise
            
    async def get_account_hierarchy(self, customer_id: str) -> Dict[str, Any]:
        """Get the account hierarchy tree."""
        try:
            client = self.auth_manager.get_client(customer_id)
            googleads_service = client.get_service("GoogleAdsService")
            
            query = """
                SELECT
                    customer_client.id,
                    customer_client.descriptive_name,
                    customer_client.manager,
                    customer_client.level,
                    customer_client.time_zone,
                    customer_client.currency_code
                FROM customer_client
                WHERE customer_client.level <= 2
            """
            
            response = googleads_service.search(
                customer_id=customer_id,
                query=query,
            )
            
            hierarchy = []
            for row in response:
                hierarchy.append({
                    "id": str(row.customer_client.id),
                    "name": row.customer_client.descriptive_name,
                    "is_manager": row.customer_client.manager,
                    "level": row.customer_client.level,
                    "time_zone": row.customer_client.time_zone,
                    "currency_code": row.customer_client.currency_code,
                })
                
            return {
                "success": True,
                "hierarchy": hierarchy,
                "count": len(hierarchy),
            }
            
        except Exception as e:
            logger.error(f"Failed to get account hierarchy: {e}")
            raise

    # ---- Advanced handlers (recommendations, change history, geo search) ----

    async def get_recommendations(self, customer_id: str, recommendation_type: Optional[str] = None,
                                  limit: int = 50) -> Dict[str, Any]:
        """List optimization recommendations for the account."""
        try:
            client = self.auth_manager.get_client(customer_id)
            ga = client.get_service("GoogleAdsService")
            q = ("SELECT recommendation.resource_name, recommendation.type, "
                 "recommendation.dismissed, campaign.name, campaign.id "
                 "FROM recommendation")
            if recommendation_type:
                q += f" WHERE recommendation.type = '{recommendation_type.upper()}'"
            q += f" LIMIT {int(limit)}"
            recs = []
            for row in ga.search(customer_id=customer_id, query=q):
                recs.append({
                    "resource_name": row.recommendation.resource_name,
                    "type": row.recommendation.type_.name,
                    "dismissed": row.recommendation.dismissed,
                    "campaign_id": str(row.campaign.id) if row.campaign.id else None,
                    "campaign_name": row.campaign.name or None,
                })
            return {"success": True, "recommendations": recs, "count": len(recs)}
        except GoogleAdsException as e:
            logger.error(f"Failed to get recommendations: {e}")
            return self.error_handler.format_error_response(e)

    async def apply_recommendation(self, customer_id: str, recommendation_resource_name: str,
                                   validate_only: bool = False) -> Dict[str, Any]:
        """Apply a recommendation by resource name."""
        try:
            from .utils import run_mutate
            client = self.auth_manager.get_client(customer_id)
            svc = client.get_service("RecommendationService")
            op = client.get_type("ApplyRecommendationOperation")
            op.resource_name = recommendation_resource_name
            request = client.get_type("ApplyRecommendationRequest")
            request.customer_id = str(customer_id).replace("-", "")
            request.operations.append(op)
            request.validate_only = validate_only
            resp = svc.apply_recommendation(request=request)
            return {
                "success": True,
                "applied": [r.resource_name for r in resp.results],
                "validate_only": validate_only,
            }
        except GoogleAdsException as e:
            logger.error(f"Failed to apply recommendation: {e}")
            return self.error_handler.format_error_response(e)

    async def dismiss_recommendation(self, customer_id: str,
                                     recommendation_resource_name: str) -> Dict[str, Any]:
        """Dismiss (hide) a recommendation by resource name."""
        try:
            client = self.auth_manager.get_client(customer_id)
            svc = client.get_service("RecommendationService")
            op = client.get_type("DismissRecommendationRequest.DismissRecommendationOperation")
            op.resource_name = recommendation_resource_name
            request = client.get_type("DismissRecommendationRequest")
            request.customer_id = str(customer_id).replace("-", "")
            request.operations.append(op)
            resp = svc.dismiss_recommendation(request=request)
            return {"success": True, "dismissed": [r.resource_name for r in resp.results]}
        except GoogleAdsException as e:
            logger.error(f"Failed to dismiss recommendation: {e}")
            return self.error_handler.format_error_response(e)

    async def get_change_history(self, customer_id: str, days_ago: int = 14,
                                 limit: int = 200) -> Dict[str, Any]:
        """Get recent account changes from the change_event resource."""
        try:
            days_ago = max(1, min(int(days_ago), 29))  # API allows the last 30 days
            client = self.auth_manager.get_client(customer_id)
            ga = client.get_service("GoogleAdsService")
            start = (datetime.utcnow().date() - timedelta(days=days_ago)).strftime("%Y-%m-%d")
            end = datetime.utcnow().date().strftime("%Y-%m-%d")
            q = f"""
                SELECT change_event.change_date_time, change_event.change_resource_type,
                    change_event.resource_change_operation, change_event.user_email,
                    change_event.client_type, change_event.changed_fields,
                    change_event.campaign, change_event.ad_group
                FROM change_event
                WHERE change_event.change_date_time >= '{start}'
                    AND change_event.change_date_time <= '{end} 23:59:59'
                ORDER BY change_event.change_date_time DESC
                LIMIT {int(limit)}
            """
            changes = []
            for row in ga.search(customer_id=customer_id, query=q):
                ce = row.change_event
                changes.append({
                    "when": ce.change_date_time,
                    "resource_type": ce.change_resource_type.name,
                    "operation": ce.resource_change_operation.name,
                    "user": ce.user_email,
                    "client_type": ce.client_type.name,
                    "changed_fields": list(ce.changed_fields.paths) if ce.changed_fields.paths else [],
                    "campaign": ce.campaign or None,
                    "ad_group": ce.ad_group or None,
                })
            return {"success": True, "changes": changes, "count": len(changes)}
        except GoogleAdsException as e:
            logger.error(f"Failed to get change history: {e}")
            return self.error_handler.format_error_response(e)

    async def search_geo_targets(self, customer_id: str, names: List[str],
                                 country_code: str = "IN", locale: str = "en") -> Dict[str, Any]:
        """Resolve place names to geo target constants for location targeting."""
        try:
            client = self.auth_manager.get_client(customer_id)
            gtc = client.get_service("GeoTargetConstantService")
            req = client.get_type("SuggestGeoTargetConstantsRequest")
            req.locale = locale
            req.country_code = country_code
            for n in names:
                req.location_names.names.append(n)
            resp = gtc.suggest_geo_target_constants(request=req)
            out = []
            for s in resp.geo_target_constant_suggestions:
                g = s.geo_target_constant
                out.append({
                    "resource_name": g.resource_name,
                    "id": str(g.id),
                    "name": g.name,
                    "canonical_name": g.canonical_name,
                    "target_type": g.target_type,
                    "country_code": g.country_code,
                    "reach": s.reach,
                })
            return {"success": True, "results": out, "count": len(out)}
        except GoogleAdsException as e:
            logger.error(f"Failed to search geo targets: {e}")
            return self.error_handler.format_error_response(e)

    def _register_search_intelligence_tools(self) -> Dict[str, Dict[str, Any]]:
        """Register search terms analysis and negative keyword intelligence tools."""
        return {
            "auto_suggest_negative_keywords": {
                "description": "Auto-suggest negative keywords based on wasteful search terms analysis",
                "handler": self.keyword_tools.auto_suggest_negative_keywords,
                "parameters": {
                    "customer_id": {"type": "string", "required": True},
                    "campaign_id": {"type": "string"},
                    "ad_group_id": {"type": "string"},
                    "date_range": {"type": "string", "default": "LAST_30_DAYS"},
                    "min_cost": {"type": "number", "default": 5.0},
                    "max_suggestions": {"type": "number", "default": 50},
                },
            },
            "get_search_terms_insights": {
                "description": "Get comprehensive search terms analysis with keyword expansion opportunities",
                "handler": self.keyword_tools.get_search_terms_insights,
                "parameters": {
                    "customer_id": {"type": "string", "required": True},
                    "campaign_id": {"type": "string"},
                    "ad_group_id": {"type": "string"},
                    "date_range": {"type": "string", "default": "LAST_30_DAYS"},
                    "min_impressions": {"type": "number", "default": 5},
                },
            },
        }
    
    def _register_audience_tools(self) -> Dict[str, Dict[str, Any]]:
        """Register audience management and targeting tools."""
        return {
            "create_custom_audience": {
                "description": "Create a custom audience for targeting (remarketing, customer match)",
                "handler": self.audience_tools.create_custom_audience,
                "parameters": {
                    "customer_id": {"type": "string", "required": True},
                    "name": {"type": "string", "required": True},
                    "audience_type": {"type": "string", "required": True},
                    "rules": {"type": "object", "required": True},
                    "description": {"type": "string"},
                },
            },
            "add_audience_targeting": {
                "description": "Add audience targeting to an ad group. SYNTAX: audience_id can be just ID ('375' for user interests, '9088079237' for user lists) or full resource name ('customers/123/userLists/456'). Tool auto-detects type: 8+ digits = user list, shorter = user interest.",
                "handler": self.audience_tools.add_audience_targeting,
                "parameters": {
                    "customer_id": {"type": "string", "required": True},
                    "ad_group_id": {"type": "string", "required": True},
                    "audience_id": {"type": "string", "required": True, "description": "User interest ID ('375'), user list ID ('9088079237'), or full resource name ('customers/123/userLists/456')"},
                    "targeting_mode": {"type": "string", "default": "TARGETING", "description": "TARGETING or OBSERVATION"},
                    "bid_modifier": {"type": "number", "description": "Bid adjustment, e.g. 1.2 for +20%"},
                },
            },
            "list_audiences": {
                "description": "List all available audiences/user lists",
                "handler": self.audience_tools.list_audiences,
                "parameters": {
                    "customer_id": {"type": "string", "required": True},
                    "audience_type": {"type": "string"},
                },
            },
            "get_audience_performance": {
                "description": "Get performance data for audience targeting",
                "handler": self.audience_tools.get_audience_performance,
                "parameters": {
                    "customer_id": {"type": "string", "required": True},
                    "audience_id": {"type": "string"},
                    "campaign_id": {"type": "string"},
                    "date_range": {"type": "string", "default": "LAST_30_DAYS"},
                },
            },
        }
    
    def _register_geography_tools(self) -> Dict[str, Dict[str, Any]]:
        """Register geographic performance and targeting tools."""
        return {
            "get_location_performance": {
                "description": "Get performance data by geographic location with optimization insights",
                "handler": self.geography_tools.get_location_performance,
                "parameters": {
                    "customer_id": {"type": "string", "required": True},
                    "campaign_id": {"type": "string"},
                    "date_range": {"type": "string", "default": "LAST_30_DAYS"},
                    "location_type": {"type": "string", "default": "COUNTRY_AND_REGION"},
                },
            },
            "optimize_geographic_targeting": {
                "description": "Auto-analyze geographic performance and suggest targeting optimizations",
                "handler": self.geography_tools.optimize_geographic_targeting,
                "parameters": {
                    "customer_id": {"type": "string", "required": True},
                    "campaign_id": {"type": "string", "required": True},
                    "date_range": {"type": "string", "default": "LAST_30_DAYS"},
                    "min_cost_threshold": {"type": "number", "default": 20.0},
                    "poor_roas_threshold": {"type": "number", "default": 1.0},
                },
            },
        }
    
    def _register_bidding_tools(self) -> Dict[str, Dict[str, Any]]:
        """Register bidding strategy and bid adjustment tools."""
        return {
            "set_bid_adjustments": {
                "description": "Set bid adjustments for campaign (device, location, demographic)",
                "handler": self.bidding_tools.set_bid_adjustments,
                "parameters": {
                    "customer_id": {"type": "string", "required": True},
                    "campaign_id": {"type": "string", "required": True},
                    "adjustments": {"type": "object", "required": True},
                },
            },
            "get_bid_adjustment_performance": {
                "description": "Get performance data for current bid adjustments",
                "handler": self.bidding_tools.get_bid_adjustment_performance,
                "parameters": {
                    "customer_id": {"type": "string", "required": True},
                    "campaign_id": {"type": "string", "required": True},
                    "date_range": {"type": "string", "default": "LAST_30_DAYS"},
                },
            },
            "create_portfolio_bidding_strategy": {
                "description": "Create a portfolio bidding strategy for sharing across campaigns. For TARGET_IMPRESSION_SHARE, use strategy_config with location, impression_share_target, and optionally max_cpc_bid_limit_micros.",
                "handler": self.bidding_tools.create_portfolio_bidding_strategy,
                "parameters": {
                    "customer_id": {"type": "string", "required": True},
                    "name": {"type": "string", "required": True},
                    "strategy_type": {"type": "string", "required": True},
                    "target_cpa_micros": {"type": "number"},
                    "target_roas": {"type": "number"},
                    "strategy_config": {"type": "object"},
                },
            },
            "list_bidding_strategies": {
                "description": "List all bidding strategies in the account",
                "handler": self.bidding_tools.list_bidding_strategies,
                "parameters": {
                    "customer_id": {"type": "string", "required": True},
                },
            },
            "get_device_performance": {
                "description": "Get performance breakdown by device type (mobile, desktop, tablet)",
                "handler": self.bidding_tools.get_device_performance,
                "parameters": {
                    "customer_id": {"type": "string", "required": True},
                    "campaign_id": {"type": "string"},
                    "date_range": {"type": "string", "default": "LAST_30_DAYS"},
                },
            },
        }
    
    # (Account, Ad Group, Ad, Asset, Budget, Keyword, and Advanced tools)
    # These would follow the same pattern as the campaign and reporting tools