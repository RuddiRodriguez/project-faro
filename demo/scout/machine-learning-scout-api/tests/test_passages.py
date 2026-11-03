from unittest import TestCase
from unittest.mock import Mock, patch
from scout.passages import split_text
from scout.searcher import Searcher
from scout.searcher_input import SearcherInput
from api_objects.faro.connector.output.connector_output import SourceItem


class PassageTests(TestCase):
    def test_exact_positions_and_overlap(self):
        text = "  " + "Record 0042: 19.75 hours.\n" * 120
        parts = list(split_text(text))
        self.assertGreater(len(parts), 2)
        for start, end, chunk in parts:
            self.assertEqual(chunk, text[start:end])
            self.assertLessEqual(end-start, 1000)
        for first, second in zip(parts, parts[1:]):
            self.assertLess(second[0], first[1])
        self.assertEqual(parts[-1][1], len(text.rstrip()))

    def test_search_keeps_pages_separate(self):
        item = SourceItem(id="report/pages", kind="pdf", location="report.pdf#pages", fields=["page", "text"], scope_ids=["north"], version="v1")
        client=Mock(); captured=[]
        def prepare(company, items, load_text):
            captured.extend(load_text()); client.indexes={"key":(None, captured)}
            return "key"
        client.prepare.side_effect=prepare
        searcher=Searcher(client)
        searcher.retriever=Mock()
        searcher.retriever.search.return_value=Mock(is_success=True,hits=[])
        with patch("scout.searcher.sources",side_effect=[Mock(items=[item]),Mock(rows=[dict(page=1,text="First page"),dict(page=2,text="Second page")])]):
            searcher.search(SearcherInput(company_id="client",query="page",permitted_scope_ids=["north"]))
        self.assertEqual([p["page"] for p in captured],[1,2])
        self.assertEqual([p["text"] for p in captured],["First page","Second page"])
        self.assertTrue(all(p["source_id"]==item.id for p in captured))
