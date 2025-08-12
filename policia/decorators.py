from django.shortcuts import render, redirect
#from .common_lib import get_adviser, get_client

def group_required(*group_names):
    def _method_wrapper(f):
        def _arguments_wrapper(request, *args, **kwargs) :
            if request.user.is_authenticated:
                if bool(request.user.groups.filter(name__in=group_names)) or request.user.is_superuser:
                    return f(request, *args, **kwargs)
#                    adviser = get_adviser(request.user)
#                    if adviser != None:
#                        request.adviser = adviser
#                        return f(request, *args, **kwargs)
#                    else:
#                        client = get_client(request.user)
#                        if client != None:
#                            request.client = client
#                            return f(request, *args, **kwargs)
#                        else:
#                            return (render(request, "generic/error_exception.html", {'exc':"This user is not adviser"}))
                else:
                	return (render(request, "error_exception.html", {'exc':"This user have not permission to access to this section"}))
            return redirect('auth_login')
        return _arguments_wrapper
    return _method_wrapper

def group_required_pwa(*group_names):
    def _method_wrapper(f):
        def _arguments_wrapper(request, *args, **kwargs) :
            if request.user.is_authenticated:
                if bool(request.user.groups.filter(name__in=group_names)) or request.user.is_superuser:
                    return f(request, *args, **kwargs)
                else:
                	return (render(request, "error_exception.html", {'exc':"This user have not permission to access to this section"}))
            return redirect('pwa-login')
        return _arguments_wrapper
    return _method_wrapper

