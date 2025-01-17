"""
Trainer module tests
"""

import os
import unittest
import tempfile

import torch

from transformers import AutoTokenizer, AutoModelForSequenceClassification

from txtai.pipeline import HFTrainer, Labels


class TestTrainer(unittest.TestCase):
    """
    Trainer tests
    """

    @classmethod
    def setUpClass(cls):
        """
        Create default datasets
        """

        cls.data = [{"text": "Dogs", "label": 0}, {"text": "dog", "label": 0}, {"text": "Cats", "label": 1}, {"text": "cat", "label": 1}] * 100

    def testBasic(self):
        """
        Test training a model with basic parameters
        """

        trainer = HFTrainer()
        model, tokenizer = trainer("google/bert_uncased_L-2_H-128_A-2", self.data)

        labels = Labels((model, tokenizer), dynamic=False)
        self.assertEqual(labels("cat")[0][0], 1)

    def testCustom(self):
        """
        Test training a model with custom parameters
        """

        model = AutoModelForSequenceClassification.from_pretrained("google/bert_uncased_L-2_H-128_A-2")
        tokenizer = AutoTokenizer.from_pretrained("google/bert_uncased_L-2_H-128_A-2")

        trainer = HFTrainer()
        model, tokenizer = trainer(
            (model, tokenizer),
            self.data,
            self.data,
            columns=("text", "label"),
            do_eval=True,
            output_dir=os.path.join(tempfile.gettempdir(), "trainer"),
        )

        labels = Labels((model, tokenizer), dynamic=False)
        self.assertEqual(labels("cat")[0][0], 1)

    def testDataframe(self):
        """
        Test training a model with a mock pandas DataFrame
        """

        # pylint: disable=W0613
        def to_dict(orient):
            return self.data

        df = unittest.mock.Mock(spec=["to_dict"])
        df.to_dict = to_dict

        trainer = HFTrainer()
        model, tokenizer = trainer("google/bert_uncased_L-2_H-128_A-2", df)

        labels = Labels((model, tokenizer), dynamic=False)
        self.assertEqual(labels("cat")[0][0], 1)

    def testDataset(self):
        """
        Test training a model with a mock Hugging Face Dataset
        """

        class TestDataset(torch.utils.data.Dataset):
            """
            Test Dataset
            """

            def __init__(self, data):
                self.data = data
                self.unique = lambda _: [0, 1]

            def __len__(self):
                return len(self.data)

            def __getitem__(self, index):
                return self.data[index]

            def map(self, fn):
                """
                Map each dataset row using fn.

                Args:
                    fn: function

                Returns:
                    updated Dataset
                """

                self.data = [fn(x) for x in self.data]
                return self

        ds = TestDataset(self.data)

        trainer = HFTrainer()
        model, tokenizer = trainer("google/bert_uncased_L-2_H-128_A-2", ds)

        labels = Labels((model, tokenizer), dynamic=False)
        self.assertEqual(labels("cat")[0][0], 1)

    def testRegression(self):
        """
        Tests training a model with a regression (continuous) output.
        """

        data = []
        for x in self.data:
            x["label"] = float(x["label"])
            data.append(x)

        trainer = HFTrainer()
        model, tokenizer = trainer("google/bert_uncased_L-2_H-128_A-2", data)

        labels = Labels((model, tokenizer), dynamic=False)

        # Regression tasks return a single entry with the regression output
        self.assertGreater(labels("cat")[0][1], 0.5)
