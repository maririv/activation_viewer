import json

from django.core.exceptions import PermissionDenied
from django.template import RequestContext
from django.shortcuts import render_to_response
from django.http import HttpResponse

from taggit.models import Tag
from guardian.shortcuts import get_perms

from geonode.security.views import _perms_info_json
from geonode.maps.models import Map

from .models import Activation, ExternalLayer

_PERMISSION_MSG_VIEW = "You are not permitted to view this activation"

def _resolve_activation(request, activation_id, permission='activation.view_activation',
                   msg=_PERMISSION_MSG_VIEW):
    """
    Resolve the activation by the provided activation_id and check the optional permission.
    """
    activation = Activation.objects.get(activation_id=activation_id)
    if not request.user.has_perm(permission, activation):
        raise PermissionDenied(msg)

    return activation

def activation_detail(request, activation_id, template="activation_detail.html"):
    activation = _resolve_activation(request, activation_id)
    context_dict = {
        'activation': activation,
        'act_lat': activation.bbox_y0 + abs(activation.bbox_y1  - activation.bbox_y0 )/2,
        'act_lon': activation.bbox_x0 + abs(activation.bbox_x1  - activation.bbox_x0 )/2,
        'perms_list': get_perms(request.user, activation),
        'related_maps': Map.objects.filter(keywords__slug__in=Tag.objects.filter(name=activation.activation_id)),
        'external_layers': ExternalLayer.objects.filter(activation=activation)
    }
    return render_to_response(template, RequestContext(request, context_dict))

def activation_permissions(request, activation_id):
    activation = _resolve_activation(request, activation_id)

    if request.method == 'POST':
        permission_spec = json.loads(request.body)
        activation.set_permissions(permission_spec)

        return HttpResponse(
            json.dumps({'success': True}),
            status=200,
            mimetype='text/plain'
        )

    elif request.method == 'GET':
        permission_spec = _perms_info_json(resource)
        return HttpResponse(
            json.dumps({'success': True, 'permissions': permission_spec}),
            status=200,
            mimetype='text/plain'
        )
    else:
        return HttpResponse(
            'No methods other than get and post are allowed',
            status=401,
            mimetype='text/plain')
