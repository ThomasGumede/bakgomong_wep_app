import uuid

def handle_profile_upload(instance, filename):
    ext = filename.split('.')[-1]
    filename = '{}.{}'.format(uuid.uuid4().hex, ext)
    return f"profile/{filename}"

def handle_docs_upload(instance, filename):
    ext = filename.split('.')[-1]
    filename = '{}-{}.{}'.format(uuid.uuid4().hex, instance.user.username,ext)
    return f"profile/verify/{filename}"