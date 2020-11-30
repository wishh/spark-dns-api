from fastapi import FastAPI, Response
import checkdmarc

from OpenSSL import SSL
from cryptography import x509
from cryptography.x509.oid import NameOID
import idna
import concurrent.futures

from socket import socket
from collections import namedtuple

HostInfo = namedtuple(field_names='cert hostname peername', typename='HostInfo')

def verify_cert(cert, hostname):
    # verify notAfter/notBefore, CA trusted, servername/sni/hostname
    cert.has_expired()
    # service_identity.pyopenssl.verify_hostname(client_ssl, hostname)
    # issuer

def get_certificate(hostname):
    hostname_idna = idna.encode(hostname)
    sock = socket()

    sock.connect((hostname, 433))
    peername = sock.getpeername()
    ctx = SSL.Context(SSL.SSLv23_METHOD) # most compatible
    ctx.check_hostname = False
    ctx.verify_mode = SSL.VERIFY_NONE

    sock_ssl = SSL.Connection(ctx, sock)
    sock_ssl.set_connect_state()
    sock_ssl.set_tlsext_host_name(hostname_idna)
    sock_ssl.do_handshake()
    cert = sock_ssl.get_peer_certificate()
    crypto_cert = cert.to_cryptography()
    sock_ssl.close()
    sock.close()

    return HostInfo(cert=crypto_cert, peername=peername, hostname=hostname)

def get_alt_names(cert):
    try:
        ext = cert.extensions.get_extension_for_class(x509.SubjectAlternativeName)
        return ext.value.get_values_for_type(x509.DNSName)
    except x509.ExtensionNotFound:
        return None

def get_common_name(cert):
    try:
        names = cert.subject.get_attributes_for_oid(NameOID.COMMON_NAME)
        return names[0].value
    except x509.ExtensionNotFound:
        return None

def get_issuer(cert):
    try:
        names = cert.issuer.get_attributes_for_oid(NameOID.COMMON_NAME)
        return names[0].value
    except x509.ExtensionNotFound:
        return None


def print_basic_info(hostinfo):
    s = '''» {hostname} « … {peername}
    \tcommonName: {commonname}
    \tSAN: {SAN}
    \tissuer: {issuer}
    \tnotBefore: {notbefore}
    \tnotAfter:  {notafter}
    '''.format(
            hostname=hostinfo.hostname,
            peername=hostinfo.peername,
            commonname=get_common_name(hostinfo.cert),
            SAN=get_alt_names(hostinfo.cert),
            issuer=get_issuer(hostinfo.cert),
            notbefore=hostinfo.cert.not_valid_before,
            notafter=hostinfo.cert.not_valid_after
    )
    print(s)

def check_it_out(hostname):
    hostinfo = get_certificate(hostname)
    print_basic_info(hostinfo)

app = FastAPI()

@app.get("/api/dnssearch/{domain}")
async def check_domain(domain: str, response: Response):
    response.headers["Access-Control-Allow-Origin"] = "*"
    search = checkdmarc.check_domains([domain], include_dmarc_tag_descriptions=True)

    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as e:
        for hostinfo in e.map(lambda x: get_certificate(x[0], x[1]), domain):
            print_basic_info(hostinfo)


    return search, print_basic_info
