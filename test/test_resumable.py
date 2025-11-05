from treadmill_monitor.processors import ResumeableTreadmillUpdateProcessor

def test_resumable():
    processor = ResumeableTreadmillUpdateProcessor()

    assert processor.process("time_elapsed", 0) == 0
    assert processor.process("time_elapsed", 10) == 10
    assert processor.process("time_elapsed", 0) == 10
    assert processor.process("time_elapsed", 10) == 20
    assert processor.process("time_elapsed", 0) == 20