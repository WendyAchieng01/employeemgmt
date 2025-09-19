from django.utils.deprecation import MiddlewareMixin

class RedirectToLoginMiddleware(MiddlewareMixin):
    def process_response(self, request, response):
        # If the response is a redirect to login, add the current path as next parameter
        if response.status_code == 302 and 'login' in response.url:
            login_url = response.url
            if 'next=' not in login_url:
                current_path = request.get_full_path()
                response['Location'] = f"{login_url}?next={current_path}"
        return response