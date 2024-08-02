from datetime import timedelta, datetime, timezone

from fastapi import APIRouter, HTTPException
from fastapi import status as http_status

from modules.insights.aggregation import NewsInsightCardModel, CoinImpactCardModel
from modules.api.auxiliary.dependencies import AggregationServiceDep, ConfigManagerDep
from modules.app.config import Configs

insights_api_router = APIRouter(prefix='/insights', tags=['insights'])


@insights_api_router.get('/news/latest_insights', response_model=list[NewsInsightCardModel], summary='Latest Insights', description=' ')
def get_latest_insights(page: int, page_size: int,
                        aggregation_service: AggregationServiceDep,
                        config_manager: ConfigManagerDep):
    if page <= 0 or page_size <= 0:
        raise HTTPException(http_status.HTTP_400_BAD_REQUEST, 'Invalid page or page size')

    config = config_manager.get_config(Configs.public_api)
    insights_limit = config.latest_insights_limit

    if page * page_size > insights_limit:
        raise HTTPException(http_status.HTTP_403_FORBIDDEN, 'The limit of available insights has been exceeded')

    release_delay = timedelta(seconds=config.latest_insights_delay_seconds)
    insights = aggregation_service.get_latest_news_insights(insights_count=page_size, offset=(page - 1) * page_size,
                                                            delay=release_delay)
    return insights


@insights_api_router.get('/coins/top_impact', response_model=list[CoinImpactCardModel],
                         summary='Top Impact Coins', description='Static window 24h top impact coins. Updated every hour')
def get_top_impact_coins(aggregation_service: AggregationServiceDep,
                         config_manager: ConfigManagerDep):
    top_limit = config_manager.get_config(Configs.public_api).top_impact_coins_24h_limit
    return aggregation_service.get_daily_top_impact_coins(timestamp=datetime.now(timezone.utc), top_count=top_limit)


@insights_api_router.get('/coins/public_highlight', response_model=list[CoinImpactCardModel],
                         summary='Public Highlighted Coins', description='Static window 24h public highlighted coins')
def get_public_highlighted_coins(aggregation_service: AggregationServiceDep,
                                 config_manager: ConfigManagerDep):
    top_limit = config_manager.get_config(Configs.public_api).public_highlight_24h_limit
    return aggregation_service.get_daily_top_referenced_coins(timestamp=datetime.now(timezone.utc), top_count=top_limit)

