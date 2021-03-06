# coding: utf-8
import threading
from BaseHTTPServer import BaseHTTPRequestHandler
from BaseHTTPServer import HTTPServer
from SocketServer import ThreadingMixIn

import xbmc

from resources.lib import logger
from resources.lib import magnetic
from resources.lib.utils import PROVIDER_SERVICE_HOST, PROVIDER_SERVICE_PORT, ADDON_VERSION


class ThreadedHTTPServer(ThreadingMixIn, HTTPServer):
    daemon_threads = True
    allow_reuse_address = True
    """Handle requests in a separate thread."""


# noinspection PyPep8Naming
class ProvidersHandler(BaseHTTPRequestHandler):
    def _write_headers(self):
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()

    def log_message(self, format_message, *args):
        pass

    def do_HEAD(self):
        self._write_headers()

    # provider addon callback to append results to response
    def do_POST(self):
        magnetic.process_provider(self)

    # kodi call to get results
    def do_GET(self):
        self._write_headers()
        self.wfile.write(magnetic.get_results(self))


if __name__ == '__main__':
    from BaseHTTPServer import HTTPServer

    server = ThreadedHTTPServer((PROVIDER_SERVICE_HOST, PROVIDER_SERVICE_PORT), ProvidersHandler)
    logger.log.info('')
    logger.log.info('                          _   _')
    logger.log.info(' _ __  __ _ __ _ _ _  ___| |_(_)__')
    logger.log.info("| '  \/ _' / _' | ' \/ -_)  _| / _|")
    logger.log.info('|_|_|_\__,_\__, |_||_\___|\__|_\__|')
    logger.log.info('          |___/')
    logger.log.info('')
    logger.log.info('Version: %s' % ADDON_VERSION)
    logger.log.info('Magnetic service at ' + str(PROVIDER_SERVICE_HOST) + ":" + str(PROVIDER_SERVICE_PORT))
    threading.Timer(0, server.serve_forever).start()
    while not xbmc.abortRequested:
        xbmc.sleep(1500)
    server.shutdown()
    logger.log.info("Exiting providers service")
