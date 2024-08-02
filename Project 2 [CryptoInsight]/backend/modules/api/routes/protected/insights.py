from datetime import timedelta, datetime, timezone, date
from typing import Annotated

from fastapi import APIRouter, HTTPException, Query, Security
from fastapi import status as http_status

from modules.api.auxiliary.oauth2 import user_auth
from modules.app.user import AccessScopes
from modules.binance.engine import BinanceIntervals
from modules.insights.aggregation import NewsInsightModel, NewsInsightCardModel, CoinImpactCardModel, \
    NewsInsightMapStackModel, CompositeMarketCandle
from modules.api.auxiliary.dependencies import AggregationServiceDep, ConfigManagerDep, UserManagerDep
from modules.app.config import Configs
from modules.tools import get_scope_description

insights_api_router = APIRouter(prefix='/insights', tags=['insights'])


@insights_api_router.get('/news/insight', response_model=NewsInsightModel, summary='News Insight Content',
                         description=get_scope_description([AccessScopes.access_tier_1.value]))
def get_latest_news_insights(token: Annotated[str, Query(min_length=32, max_length=32)],
                             user_token: Annotated[
                                 dict, Security(user_auth, scopes=[AccessScopes.access_tier_1.value])],
                             user_manager: UserManagerDep,
                             config_manager: ConfigManagerDep,
                             aggregation_service: AggregationServiceDep):
    insight = aggregation_service.get_news_insight(token)
    if insight is None:
        raise HTTPException(http_status.HTTP_404_NOT_FOUND, 'Insight not found')

    user_scopes = user_manager.get_user_scopes(user_token)

    if AccessScopes.access_tier_2 not in user_scopes:
        time_limit = config_manager.get_config(Configs.protected_api).insights_archive_deep_limit_days
        archive_deep_limit = datetime.now(timezone.utc) - timedelta(days=time_limit)
        if insight.release_time.replace(tzinfo=timezone.utc) < archive_deep_limit:
            raise HTTPException(http_status.HTTP_403_FORBIDDEN, 'Access to the archive is forbidden')

    return insight


@insights_api_router.get('/news/brief_insights', response_model=list[NewsInsightCardModel],
                         summary='Brief News Insights',
                         description=get_scope_description([AccessScopes.access_tier_1.value]))
def get_brief_news_insights(start_time: datetime, end_time: datetime,
                            user_token: Annotated[dict, Security(user_auth, scopes=[AccessScopes.access_tier_1.value])],
                            user_manager: UserManagerDep,
                            config_manager: ConfigManagerDep,
                            aggregation_service: AggregationServiceDep,
                            coin_filter: Annotated[str, Query(min_length=1, max_length=15)] = None):
    start_time = start_time.replace(tzinfo=timezone.utc)
    end_time = end_time.replace(tzinfo=timezone.utc)

    if start_time > end_time:
        raise HTTPException(http_status.HTTP_400_BAD_REQUEST, 'The start time must be less than the end time')

    user_scopes = user_manager.get_user_scopes(user_token)
    if AccessScopes.access_tier_2 not in user_scopes:
        time_limit = config_manager.get_config(Configs.protected_api).insights_archive_deep_limit_days
        archive_deep_limit = datetime.now(timezone.utc) - timedelta(days=time_limit)
        if start_time < archive_deep_limit:
            raise HTTPException(http_status.HTTP_403_FORBIDDEN, 'Access to the archive is forbidden')

    insights = aggregation_service.get_news_insights_range(start_time=start_time, end_time=end_time,
                                                           symbol_pair=coin_filter)
    return insights


@insights_api_router.get('/news/insight_map', response_model=list[NewsInsightMapStackModel], summary='News Insight Map',
                         description=get_scope_description([AccessScopes.access_tier_1.value]))
def get_news_insight_map(start_date: date, end_date: date,
                         user_token: Annotated[dict, Security(user_auth, scopes=[AccessScopes.access_tier_1.value])],
                         user_manager: UserManagerDep,
                         aggregation_service: AggregationServiceDep,
                         config_manager: ConfigManagerDep):
    start_date = datetime.combine(start_date, datetime.min.time()).replace(tzinfo=timezone.utc)
    end_date = datetime.combine(end_date, datetime.min.time()).replace(tzinfo=timezone.utc)
    if start_date > end_date:
        raise HTTPException(http_status.HTTP_400_BAD_REQUEST, 'The start date must be less than the end date')

    user_scopes = user_manager.get_user_scopes(user_token)
    if AccessScopes.access_tier_2 not in user_scopes:
        time_limit = config_manager.get_config(Configs.protected_api).insights_archive_deep_limit_days
        archive_deep_limit = datetime.now(timezone.utc) - timedelta(days=time_limit)
        if start_date < archive_deep_limit:
            raise HTTPException(http_status.HTTP_403_FORBIDDEN, 'Access to the archive is forbidden')

    stacks = aggregation_service.get_news_insight_map(start_time=start_date, end_time=end_date)
    return stacks


@insights_api_router.get('/coins/top_impact', response_model=list[CoinImpactCardModel], summary='Top Impact Coins',
                         description=get_scope_description([AccessScopes.access_tier_1.value]))
def get_top_impact_coins(target_date: date,
                         user_token: Annotated[dict, Security(user_auth, scopes=[AccessScopes.access_tier_1.value])],
                         user_manager: UserManagerDep,
                         aggregation_service: AggregationServiceDep,
                         config_manager: ConfigManagerDep):
    target_date = datetime.combine(target_date, datetime.min.time()).replace(tzinfo=timezone.utc)
    user_scopes = user_manager.get_user_scopes(user_token)
    if AccessScopes.access_tier_2 not in user_scopes:
        time_limit = config_manager.get_config(Configs.protected_api).insights_archive_deep_limit_days
        archive_deep_limit = datetime.now(timezone.utc) - timedelta(days=time_limit)
        if target_date < archive_deep_limit:
            raise HTTPException(http_status.HTTP_403_FORBIDDEN, 'Access to the archive is forbidden')

    top_limit = config_manager.get_config(Configs.protected_api).top_impact_coins_limit
    return aggregation_service.get_daily_top_impact_coins(timestamp=target_date, top_count=top_limit)


@insights_api_router.get('/coins/composite_candles', response_model=list[CompositeMarketCandle],
                         summary='Composite Candles For The Coin Chart',
                         description=get_scope_description([AccessScopes.access_tier_1.value]))
def get_coin_composite_candle(start_time: datetime, end_time: datetime,
                              interval: BinanceIntervals,
                              user_token: Annotated[dict, Security(user_auth, scopes=[AccessScopes.access_tier_1.value])],
                              user_manager: UserManagerDep,
                              aggregation_service: AggregationServiceDep,
                              config_manager: ConfigManagerDep,
                              symbol_pair: Annotated[str, Query(min_length=1, max_length=15)] = None):
    start_time = start_time.replace(tzinfo=timezone.utc)
    end_time = end_time.replace(tzinfo=timezone.utc)

    if start_time > end_time:
        raise HTTPException(http_status.HTTP_400_BAD_REQUEST, 'The start date must be less than the end date')

    if interval not in [BinanceIntervals.hours, BinanceIntervals.days]:
        raise HTTPException(http_status.HTTP_403_FORBIDDEN, 'Interval is forbidden')

    user_scopes = user_manager.get_user_scopes(user_token)
    if AccessScopes.access_tier_2 not in user_scopes:
        time_limit = config_manager.get_config(Configs.protected_api).insights_archive_deep_limit_days
        archive_deep_limit = datetime.now(timezone.utc) - timedelta(days=time_limit)
        if start_time < archive_deep_limit:
            raise HTTPException(http_status.HTTP_403_FORBIDDEN, 'Access to the archive is forbidden')

    candles = aggregation_service.get_coin_composite_candles(start_time=start_time, end_time=end_time,
                                                             symbol_pair=symbol_pair, interval=interval)
    return candles

