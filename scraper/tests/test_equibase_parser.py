from datetime import date
from decimal import Decimal

from django.test import SimpleTestCase

from scraper.clients.equibase import EquibaseClient


SAMPLE_RESULTS_HTML = """
<html><body>
Race 6
1 1/16M Turf Purse: $45,000
1st 9 Winner Horse
2nd 2 Place Horse
3rd 7 Show Horse
Final Time: 1:42.35
Win $8.40 Place $4.20 Show $3.00
Exacta $42.60 Trifecta $158.80
Race 7
6 Furlongs Dirt
1st 4
2nd 1
3rd 3
Win $5.20
</body></html>
"""


class EquibaseParserTests(SimpleTestCase):
    def test_parse_results_html(self):
        client = EquibaseClient()
        card = client.parse_results_html(SAMPLE_RESULTS_HTML, "GP", date(2026, 8, 2))
        self.assertEqual(card.track_code, "GP")
        self.assertEqual(len(card.races), 2)

        race6 = card.races[0]
        self.assertEqual(race6.race_number, 6)
        self.assertEqual(race6.status, "official")
        self.assertEqual(race6.finishers[0].program_number, "9")
        self.assertEqual(race6.winning_time, "1:42.35")

        bet_types = {p.bet_type for p in race6.payouts}
        self.assertIn("W", bet_types)
        self.assertIn("EXA", bet_types)
        self.assertIn("TRI", bet_types)
        win = next(p for p in race6.payouts if p.bet_type == "W")
        self.assertEqual(win.amount, Decimal("8.40"))

    def test_distance_to_furlongs(self):
        client = EquibaseClient()
        self.assertEqual(client._distance_to_furlongs("1 1/16M T"), Decimal("8.5"))
        self.assertEqual(client._distance_to_furlongs("6F D"), Decimal("6"))
