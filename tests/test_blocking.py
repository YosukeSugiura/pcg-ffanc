from ffanc_norm.blocking import FrameScheduler


def test_quarter_shift_overlap():
    scheduler = FrameScheduler(512, 128)
    assert scheduler.overlap_fraction == 0.75
    assert scheduler.starts(1024) == [0, 128, 256, 384, 512]


def test_hop_ranges_begin_immediately_with_zero_padded_history():
    scheduler = FrameScheduler(512, 128)
    assert scheduler.hop_ranges(512) == [
        (0, 128),
        (128, 256),
        (256, 384),
        (384, 512),
    ]
