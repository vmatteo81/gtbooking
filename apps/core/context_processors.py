def current_gym(request):
    return {"current_gym": getattr(request, "gym", None)}
