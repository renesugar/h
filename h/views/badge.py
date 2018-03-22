# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from pyramid import httpexceptions
import newrelic.agent

from h import models, search
from h.util.view import json_view


def _unauth_user_got_zero_metric(user):
    if user is None:
        newrelic.agent.record_custom_metric('Custom/Badge/UnAuthUserGotZero', 1)
    else:
        newrelic.agent.record_custom_metric('Custom/Badge/UnAuthUserGotZero', 0)


@json_view(route_name='badge')
def badge(request):
    """Return the number of public annotations on a given page.

    This is for the number that's displayed on the Chrome extension's badge.

    Certain pages are blocklisted so that the badge never shows a number on
    those pages. The Chrome extension is oblivious to this, we just tell it
    that there are 0 annotations.

    """
    uri = request.params.get('uri')

    if not uri:
        raise httpexceptions.HTTPBadRequest()

    if models.Blocklist.is_blocked(request.db, uri):
        newrelic.agent.record_custom_metric('Custom/Badge/badgeCountIsZero', 1)
        _unauth_user_got_zero_metric(request.user)
        return {'total': 0}

    query = {'uri': uri, 'limit': 0}
    result = search.Search(request, stats=request.stats).run(query)

    newrelic.agent.record_custom_metric('Custom/Badge/badgeCountIsZero', int(result.total == 0))
    if result.total > 0:
        user = 'None' if request.user is None else request.user.username
        newrelic.agent.record_custom_metric('Custom/Badge/{}GotNonZero'.format(user), 1)
    else:
        _unauth_user_got_zero_metric(request.user)
    return {'total': result.total}
