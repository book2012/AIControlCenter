from core.automation.queue import AutomationQueue


def test_automation_queue_submit():
    queue = AutomationQueue()

    item = queue.submit("/status")

    assert item["status"] == "PENDING"


def test_automation_queue_run():
    queue = AutomationQueue()

    item = queue.submit("/status")
    result = queue.run(item["id"])

    assert result["status"] == "FINISHED"
    assert result["result"]["executed"] is True


def test_automation_queue_blocks_unsafe():
    queue = AutomationQueue()

    item = queue.submit("/backup run token")
    result = queue.run(item["id"])

    assert result["status"] == "BLOCKED"
