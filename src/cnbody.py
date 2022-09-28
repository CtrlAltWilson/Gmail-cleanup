import base64, re
from bs4 import BeautifulSoup
from .rmhtml import strip_tags


def clean_body(body):
    #BODY
    body = base64.urlsafe_b64decode(body.encode('utf-8'))
    body = body.decode("utf-8")

    soup = BeautifulSoup(body,"html.parser")
    for script in soup(['script','style']):
        script.extract()
    body = soup.get_text()
    body = strip_tags(body)

    clean = re.compile('\u200c')
    body = re.sub(clean,'',body)
    body = " ".join(body.split())
    return body
