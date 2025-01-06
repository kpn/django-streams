hello_topic = "django-streams--hello-kpn"
hello_topic_enriched = "django-streams--hello-kpn-enriched"


def successed_produce_callback(metadata):
    print(f"Event send with metadata {metadata}")
