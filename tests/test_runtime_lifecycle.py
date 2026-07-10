from core.runtime.lifecycle import GracefulLifecycle


def test_graceful_lifecycle_stop():
    lifecycle = GracefulLifecycle()

    assert lifecycle.should_stop() is False

    lifecycle.request_stop()

    assert lifecycle.should_stop() is True
