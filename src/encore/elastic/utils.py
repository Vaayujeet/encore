"""Common ElasticSearch Utilities"""

import logging
from datetime import datetime, timedelta
from enum import StrEnum

from elasticsearch import Elasticsearch, NotFoundError

from django.conf import settings
from django.utils import timezone

from elastic.constants import EVENT_INDEX_PREFIX, INDEX_DATE_SUFFIX_FORMAT, NON_COMPLETE_EVENT_STATUS, FieldNames

logger = logging.getLogger("correlator.elastic")


class SearchResponseType(StrEnum):
    """Response Type for CorrelatorElastic Search response"""

    RAW = "raw"
    HIT_LIST = "list"
    FIRST_HIT = "first"
    EXACT_ONE_HIT = "exact_one"


class CorrelatorElastic(Elasticsearch):
    """Correlator Elastic"""

    _instance = {}
    _correlator_elastic = False

    # Enrich Policy Definition
    ENRICH_POLICY_DEF = {
        # NOTE: Policy Type is "match"
        # Update version, whenever the enrich policy definition is updated.
        settings.ASSET_MAPPING_POLICY: {
            "version": 0,
            "indices": settings.ASSET_MAPPING_INDEX_NAME,
            "match_field": FieldNames.ASSET_UNIQUE_ID,
            "enrich_fields": [
                FieldNames.ASSET_UNIQUE_ID,
                FieldNames.ASSET_TYPE,
                FieldNames.ASSET_REGION,
                FieldNames.PARENT_ASSET_UNIQUE_ID,
                FieldNames.PARENT_ASSET_TYPE,
            ],
        },
    }

    def __new__(cls, *args, **kwargs):
        if cls not in cls._instance:
            instance = super().__new__(cls)
            cls._instance[cls] = instance
        return cls._instance[cls]

    def __init__(self):
        # TODO: __init__ args should be available as settings
        if self._correlator_elastic:
            # Already initiated
            return

        logger.debug("Connecting to ELK Host(s) %s", settings.ELASTIC_HOST)
        if settings.USE_ELASTIC_CERT:
            super().__init__(
                settings.ELASTIC_HOST,
                ssl_assert_fingerprint=settings.ELASTIC_CERT_FINGERPRINT,
                basic_auth=(settings.ELASTIC_USER, settings.ELASTIC_PASSWORD),
            )
            logger.debug(
                "Connected to ELK Host(s) %s as User %s using Cert.", settings.ELASTIC_HOST, settings.ELASTIC_USER
            )
        elif settings.USE_ELASTIC_AUTH:
            super().__init__(settings.ELASTIC_HOST, basic_auth=(settings.ELASTIC_USER, settings.ELASTIC_PASSWORD))
            logger.debug(
                "Connected to ELK Host(s) %s as User %s using Auth.", settings.ELASTIC_HOST, settings.ELASTIC_USER
            )
        else:
            super().__init__(settings.ELASTIC_HOST)
            logger.debug("Connected to ELK Host(s) %s", settings.ELASTIC_HOST)

        self._correlator_elastic = True

    def _get_doc(self, doc_index: str, doc_id: str):
        try:
            resp = self.get(index=doc_index, id=doc_id)
            return resp.body
        except NotFoundError:
            return None

    def get_event(self, event_index: str, event_id: str):
        """Get event document if it exists"""
        return self._get_doc(event_index, event_id)

    def search(
        self,
        *,
        index=None,
        aggregations=None,
        aggs=None,
        allow_no_indices=None,
        allow_partial_search_results=None,
        analyze_wildcard=None,
        analyzer=None,
        batched_reduce_size=None,
        ccs_minimize_roundtrips=None,
        collapse=None,
        default_operator=None,
        df=None,
        docvalue_fields=None,
        error_trace=None,
        expand_wildcards=None,
        explain=None,
        ext=None,
        fields=None,
        filter_path=None,
        force_synthetic_source=None,
        from_=None,
        highlight=None,
        human=None,
        ignore_throttled=None,
        ignore_unavailable=None,
        include_named_queries_score=None,
        indices_boost=None,
        knn=None,
        lenient=None,
        max_concurrent_shard_requests=None,
        min_compatible_shard_node=None,
        min_score=None,
        pit=None,
        post_filter=None,
        pre_filter_shard_size=None,
        preference=None,
        pretty=None,
        profile=None,
        q=None,
        query=None,
        rank=None,
        request_cache=None,
        rescore=None,
        rest_total_hits_as_int=None,
        retriever=None,
        routing=None,
        runtime_mappings=None,
        script_fields=None,
        scroll=None,
        search_after=None,
        search_type=None,
        seq_no_primary_term=None,
        size=None,
        slice=None,  # pylint: disable=redefined-builtin
        sort=None,
        source=None,
        source_excludes=None,
        source_includes=None,
        stats=None,
        stored_fields=None,
        suggest=None,
        suggest_field=None,
        suggest_mode=None,
        suggest_size=None,
        suggest_text=None,
        terminate_after=None,
        timeout=None,
        track_scores=None,
        track_total_hits=None,
        typed_keys=None,
        version=None,
        body=None,
        response_type: SearchResponseType = SearchResponseType.HIT_LIST,
    ):
        response = super().search(
            index=index,
            aggregations=aggregations,
            aggs=aggs,
            allow_no_indices=allow_no_indices,
            allow_partial_search_results=allow_partial_search_results,
            analyze_wildcard=analyze_wildcard,
            analyzer=analyzer,
            batched_reduce_size=batched_reduce_size,
            ccs_minimize_roundtrips=ccs_minimize_roundtrips,
            collapse=collapse,
            default_operator=default_operator,
            df=df,
            docvalue_fields=docvalue_fields,
            error_trace=error_trace,
            expand_wildcards=expand_wildcards,
            explain=explain,
            ext=ext,
            fields=fields,
            filter_path=filter_path,
            force_synthetic_source=force_synthetic_source,
            from_=from_,
            highlight=highlight,
            human=human,
            ignore_throttled=ignore_throttled,
            ignore_unavailable=ignore_unavailable,
            include_named_queries_score=include_named_queries_score,
            indices_boost=indices_boost,
            knn=knn,
            lenient=lenient,
            max_concurrent_shard_requests=max_concurrent_shard_requests,
            min_compatible_shard_node=min_compatible_shard_node,
            min_score=min_score,
            pit=pit,
            post_filter=post_filter,
            pre_filter_shard_size=pre_filter_shard_size,
            preference=preference,
            pretty=pretty,
            profile=profile,
            q=q,
            query=query,
            rank=rank,
            request_cache=request_cache,
            rescore=rescore,
            rest_total_hits_as_int=rest_total_hits_as_int,
            retriever=retriever,
            routing=routing,
            runtime_mappings=runtime_mappings,
            script_fields=script_fields,
            scroll=scroll,
            search_after=search_after,
            search_type=search_type,
            seq_no_primary_term=seq_no_primary_term,
            size=size,
            slice=slice,
            sort=sort,
            source=source,
            source_excludes=source_excludes,
            source_includes=source_includes,
            stats=stats,
            stored_fields=stored_fields,
            suggest=suggest,
            suggest_field=suggest_field,
            suggest_mode=suggest_mode,
            suggest_size=suggest_size,
            suggest_text=suggest_text,
            terminate_after=terminate_after,
            timeout=timeout,
            track_scores=track_scores,
            track_total_hits=track_total_hits,
            typed_keys=typed_keys,
            version=version,
            body=body,
        )
        if response_type == SearchResponseType.RAW:
            return response
        _hits = response["hits"]["hits"]
        if response_type == SearchResponseType.HIT_LIST:
            return _hits
        if response_type == SearchResponseType.FIRST_HIT and _hits:
            return _hits[0]
        if response_type == SearchResponseType.EXACT_ONE_HIT and len(_hits) == 1:
            return _hits[0]
        # TODO: May want to raise exception
        return None

    # ##### Correlator Asset Mapping
    def load_asset_mapping(self, asset_map_json, exec_enrich_policy=True):
        """Load Asset Mapping Data"""

        # TODO: Delta Load
        # TODO: Make Asset Mapping Index Fields extensible
        # TODO: Error Handling
        last_upd_ts = timezone.now()
        for asset in asset_map_json:
            asset_id = asset[FieldNames.ASSET_UNIQUE_ID].strip()
            parent = (
                asset[FieldNames.PARENT_ASSET_UNIQUE_ID].strip().upper()  # for case insensitive lookup
                if asset[FieldNames.PARENT_ASSET_UNIQUE_ID] and asset[FieldNames.PARENT_ASSET_UNIQUE_ID].strip()
                else None
            )
            parent_type = (
                asset[FieldNames.PARENT_ASSET_TYPE].strip().lower()
                if asset[FieldNames.PARENT_ASSET_TYPE] and asset[FieldNames.PARENT_ASSET_TYPE].strip()
                else None
            )
            doc = {
                FieldNames.ASSET_UNIQUE_ID: asset_id.upper(),  # for case insensitive lookup
                FieldNames.ASSET_TYPE: asset[FieldNames.ASSET_TYPE].strip().lower(),
                FieldNames.ASSET_REGION: asset[FieldNames.ASSET_REGION].strip().lower(),
                FieldNames.PARENT_ASSET_UNIQUE_ID: None if parent == "-" else parent,
                FieldNames.PARENT_ASSET_TYPE: None if parent_type == "-" else parent_type,
                FieldNames.LAST_UPDATE_TS: last_upd_ts,
            }
            logger.info(doc)
            resp = self.index(
                index=settings.ASSET_MAPPING_INDEX_NAME,
                id=f"{doc[FieldNames.ASSET_REGION]}.{doc[FieldNames.ASSET_TYPE]}.{asset_id}",
                document=doc,
            )
            logger.info(resp["result"])
            # TODO: Add proper logging

        if exec_enrich_policy:
            for enrich_policy_name in self.ENRICH_POLICY_DEF:
                self.execute_enrich_policy(self.latest_enrich_policy_name(enrich_policy_name))

    # ##### Enrich Policy Functions
    def enrich_policy_exists(self, name: str) -> bool:
        """Checks if given Enrich Policy exists in ELK"""
        # TODO: Error Handling
        resp = self.enrich.get_policy(name=name)
        return bool(len(resp["policies"]))

    def execute_enrich_policy(self, name: str):
        """Execute given Enrich Policy in ELK"""
        # TODO: Error Handling
        self.enrich.execute_policy(name=name)
        logger.info("Executed enrich policy: %s", name)

    # ## Correlator Enrich Policy Functions
    @property
    def enrich_policy_definitions(self):
        """Correlator Enrich Policy Definitions"""
        return self.ENRICH_POLICY_DEF

    def latest_enrich_policy_name(self, correlator_enrich_policy_name: str):
        """Return Correlator Enrich Policy Name with latest Version defined"""
        return f"{correlator_enrich_policy_name}_v{self.ENRICH_POLICY_DEF[correlator_enrich_policy_name]['version']}"

    def create_enrich_policy(self, correlator_enrich_policy_name: str):
        """Create given Correlator Enrich Policy in ELK if it does not exist"""
        # TODO: Error Handling
        versioned_policy_name = self.latest_enrich_policy_name(correlator_enrich_policy_name)
        policy_match_def = {
            k: v for k, v in self.ENRICH_POLICY_DEF[correlator_enrich_policy_name].items() if k != "version"
        }

        if not self.enrich_policy_exists(versioned_policy_name):
            self.enrich.put_policy(
                name=versioned_policy_name,
                match=policy_match_def,
            )
            logger.info("Created enrich policy: %s", versioned_policy_name)
            self.execute_enrich_policy(versioned_policy_name)

    def delete_old_enrich_policy(self, correlator_enrich_policy_name: str):
        """Delete old Correlator Enrich Policy from ELK if they exist"""
        # TODO: Error Handling
        for v in range(self.ENRICH_POLICY_DEF[correlator_enrich_policy_name]["version"]):
            versioned_policy_name = f"{correlator_enrich_policy_name}_v{v}"
            if self.enrich_policy_exists(versioned_policy_name):
                self.enrich.delete_policy(name=versioned_policy_name)
                logger.info("Deleted enrich policy: %s", versioned_policy_name)

    # ## Correlator Other Functions
    @classmethod
    def get_nested_field_value(cls, doc_src, field_name):
        """Returns the nested field value if present in `doc_src = doc["_source"]` else return `None`"""
        if field_name and (stripped_field_name := field_name.strip()):
            _return_value = doc_src
            for sub_field_name in stripped_field_name.split("."):
                if sub_field_name in _return_value:
                    _return_value = _return_value[sub_field_name]
                else:
                    return None
            return _return_value
        return None

    def index_has_active_event_document(self, index: str) -> bool:
        """Indicates if the given index has even a single non-completed event document."""
        query = {
            "bool": {
                "should": [
                    {"term": {f"{FieldNames.EVENT_STATUS}.keyword": status}} for status in NON_COMPLETE_EVENT_STATUS
                ],
                "minimum_should_match": 1,
            }
        }
        response = self.search(index=index, query=query, size=1, response_type=SearchResponseType.RAW)
        if response["hits"]["total"]["value"]:
            return True
        return False

    @classmethod
    def event_index_age(cls, event_index, days=7):
        """Indicates if the given event index is greater than given number of days"""
        if event_index.startswith(EVENT_INDEX_PREFIX):
            creation_date = datetime.strptime(event_index.split("-")[1], INDEX_DATE_SUFFIX_FORMAT).date()
            return creation_date < datetime.now().date() - timedelta(days=days)
        raise ValueError(f"Invalid Event Index: {event_index}")
