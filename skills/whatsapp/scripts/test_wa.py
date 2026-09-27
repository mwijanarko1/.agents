#!/usr/bin/env python3
"""Session health and recovery for WhatsApp Web send."""

from __future__ import annotations

import unittest
from unittest.mock import patch

import wa

READY_SNAP = 'e12:textbox "Search or start a new chat"\ne3:button "Chats"'
STALE_SNAP = 'heading "WhatsApp"\nbutton "Chats"\ntext Unread\ntext Favorites'


class UiReadyTests(unittest.TestCase):
    def test_search_box_means_ready(self):
        self.assertTrue(wa.ui_ready(READY_SNAP))
        self.assertEqual(wa.search_box_ref(READY_SNAP), "e12")

    def test_chrome_text_without_controls_is_not_ready(self):
        self.assertFalse(wa.ui_ready(STALE_SNAP))
        self.assertIsNone(wa.search_box_ref(STALE_SNAP))


class ViewportErrorTests(unittest.TestCase):
    def test_pinchtab_500_outside_viewport(self):
        self.assertTrue(
            wa.is_viewport_error("Error 500 action click outside viewport")
        )
        self.assertFalse(wa.is_viewport_error("could not find chat search box"))


class RecoverSessionTests(unittest.TestCase):
    def test_recover_reloads_before_send_when_search_box_missing(self):
        calls: list[list[str]] = []
        snaps = [STALE_SNAP, READY_SNAP]

        def fake_run(args, **kwargs):
            calls.append(list(args))
            return type("P", (), {"stdout": "", "stderr": "", "returncode": 0})()

        def fake_snap(_server):
            return snaps.pop(0) if snaps else READY_SNAP

        with (
            patch.object(wa, "run", fake_run),
            patch.object(wa, "snap", fake_snap),
            patch.object(wa.time, "sleep", lambda *_a, **_k: None),
        ):
            server = wa.recover_session("http://127.0.0.1:9869")

        self.assertEqual(server, "http://127.0.0.1:9869")
        self.assertEqual(calls[0], ["reload"])

    def test_recover_restarts_headed_instance_if_reload_and_nav_fail(self):
        calls: list[list[str]] = []

        def fake_run(args, **kwargs):
            calls.append(list(args))
            if args[:2] == ["instance", "list"]:
                stdout = "inst_abc123 9869 headed running\n"
            else:
                stdout = ""
            return type("P", (), {"stdout": stdout, "stderr": "", "returncode": 0})()

        with (
            patch.object(wa, "run", fake_run),
            patch.object(wa, "snap", lambda _s: STALE_SNAP),
            patch.object(wa.time, "sleep", lambda *_a, **_k: None),
            patch.object(wa, "wait_for_ui", lambda *_a, **_k: False),
        ):
            with self.assertRaises(wa.WaError) as ctx:
                wa.recover_session("http://127.0.0.1:9869")

        self.assertIn(["reload"], calls)
        self.assertIn(["nav", wa.WA_URL], calls)
        self.assertIn(["instance", "restart", "inst_abc123"], calls)
        self.assertIn("restart", str(ctx.exception).lower())


class ClickRefTests(unittest.TestCase):
    def test_outside_viewport_scrolls_then_retries(self):
        calls: list[list[str]] = []

        def fake_run(args, **kwargs):
            calls.append(list(args))
            if args == ["click", "e12"] and calls.count(["click", "e12"]) == 1:
                raise wa.WaError("Error 500 action click outside viewport")
            return type("P", (), {"stdout": "", "stderr": "", "returncode": 0})()

        with patch.object(wa, "run", fake_run):
            wa.click_ref("http://127.0.0.1:9869", "e12")

        self.assertEqual(
            calls,
            [
                ["click", "e12"],
                ["scroll", "e12"],
                ["click", "e12"],
            ],
        )


if __name__ == "__main__":
    unittest.main()


class OpenThreadGuardTests(unittest.TestCase):
    SNAP_GROUP = (
        'e12:textbox "Search or start a new chat"\n'
        'e281:button "USIC Halaqah Aamina, Aarush, Ammar"\n'
        'e326:textbox "Type a message to group USIC Halaqah" val="'
    )
    SNAP_DM = (
        'e12:textbox "Search or start a new chat"\n'
        'e50:button "Ammar"\n'
        'e77:textbox "Type a message to Ammar" val="'
    )
    SNAP_SEARCH_ONLY = (
        'e12:textbox "Search or start a new chat"\n'
        'e60:listitem "Aarush Aerospace"\n'
    )

    def test_group_composer_label(self):
        self.assertEqual(wa.open_thread_composer_name(self.SNAP_GROUP), "USIC Halaqah")

    def test_dm_composer_label(self):
        self.assertEqual(wa.open_thread_composer_name(self.SNAP_DM), "Ammar")

    def test_search_panel_only_has_no_open_thread(self):
        self.assertIsNone(wa.open_thread_composer_name(self.SNAP_SEARCH_ONLY))

    def test_wrong_open_thread_does_not_match_contact(self):
        name = wa.open_thread_composer_name(self.SNAP_GROUP)
        self.assertIsNotNone(name)
        self.assertNotEqual(name.casefold(), "aarush aerospace")



class ThreadTimestampsTests(unittest.TestCase):
    SNAP_WITH_MSGS = (
        'e12:textbox "Search or start a new chat"\n'
        'e281:button "USIC Halaqah Aamina, Aarush"\n'
        'e364:button "10:59 PM Sent "\n'
        'e326:textbox "Type a message to group USIC Halaqah" val="'
    )
    SNAP_EMPTY = (
        'e12:textbox "Search or start a new chat"\n'
        'e281:button "Aarush Aerospace"\n'
        'e326:textbox "Type a message to Aarush Aerospace" val="'
    )

    def test_thread_with_messages_has_timestamps(self):
        self.assertTrue(wa.thread_has_message_timestamps(self.SNAP_WITH_MSGS))

    def test_empty_impostor_thread_has_no_timestamps(self):
        self.assertFalse(wa.thread_has_message_timestamps(self.SNAP_EMPTY))
