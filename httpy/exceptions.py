class InvalidHTTPSequence(Exception):
    # When trying to format HTTP response out of order
    pass

class ResponseFinished(Exception):
    # When trying to send HTTP data after response has finished
    pass

class AlreadySent(Exception):
    # When trying to re-send already sent HTTP data
    pass
