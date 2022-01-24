import unittest
from arxiv_alert import get_the_paper_today


class MyTestCase(unittest.TestCase):
    def test_something(self):
        query = 'cat:cs.AI'
        today_papers = get_the_paper_today(query)
        for paper in today_papers:
            print(paper.entry_id, paper.published, paper.title)


if __name__ == '__main__':
    unittest.main()
