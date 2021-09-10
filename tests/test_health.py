from sqlalchemy import text
import json

from mock_alchemy.mocking import UnifiedAlchemyMagicMock

from quarry.web.models.query import Query
from quarry.web.models.queryrun import QueryRun
from quarry.web.models.queryrevision import QueryRevision


def test_health(mocker, client):
    minutes = 5
    session = UnifiedAlchemyMagicMock(
        data=[
            (
                [
                    mocker.call.query(Query),
                    mocker.call.filter(
                        Query.last_touched
                        >= text("NOW() - INTERVAL %d MINUTE" % minutes)
                    ),
                ],
                [Query(), Query(), Query()],
            ),
            (
                [
                    mocker.call.query(QueryRevision),
                    mocker.call.filter(
                        QueryRevision.timestamp
                        >= text("NOW() - INTERVAL %d MINUTE" % minutes)
                    ),
                ],
                [QueryRevision(), QueryRevision()],
            ),
            (
                [
                    mocker.call.query(QueryRun.status),
                    mocker.call.filter(
                        QueryRun.timestamp
                        >= text("NOW() - INTERVAL %d MINUTE" % minutes)
                    ),
                ],
                [[4], [4], [1]],  # 4 == complete, 1 == failed
            ),
        ]
    )

    with mocker.patch(
        "quarry.web.connections.Connections.session",
        new_callable=mocker.PropertyMock(return_value=session),
    ):
        rval = client.get("/.health/summary/v1/%d" % minutes)
        result_dict = json.loads(rval.data.decode("utf8"))

        session.filter.assert_has_calls(
            [
                mocker.call(
                    Query.last_touched >= text("NOW() - INTERVAL %d MINUTE" % minutes)
                ),
                mocker.call(
                    QueryRevision.timestamp
                    >= text("NOW() - INTERVAL %d MINUTE" % minutes)
                ),
                mocker.call(
                    QueryRun.timestamp >= text("NOW() - INTERVAL %d MINUTE" % minutes)
                ),
            ]
        )

        print(result_dict)
        assert result_dict["queries_num"] == 3
        assert result_dict["query_revs_num"] == 2
        assert result_dict["query_run_statuses"]["complete"] == 2
        assert result_dict["query_run_statuses"]["failed"] == 1
        assert result_dict["query_run_statuses"]["superseded"] == 0
