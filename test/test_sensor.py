from craniodistractor.sensor import decode_telegram

def test_decode_telegram():
    assert (-1.234, 'K', 'T', 'O') == decode_telegram('-1.234KTO\r')
