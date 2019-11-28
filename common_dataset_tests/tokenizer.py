import unittest
from typing import List

from NMT.students.logs.tokenizer import tokenize_line
from common_dataset.diffs import FileDiff, FileStatus


class CommitMessages(unittest.TestCase):
    input = [
              "diff --git a/b5cb9bb9bf246fbd3f6bc957b5a538ea97de15ef b/6f2f19b981c9fbc66138807b4d199851a2fd13e9",
              "index b5cb9bb9bf2..6f2f19b981c 100644",
              "--- a/b5cb9bb9bf246fbd3f6bc957b5a538ea97de15ef",
              "+++ b/6f2f19b981c9fbc66138807b4d199851a2fd13e9",
              "@@ -143,20 +143,28 @@ public class RabbitMQProducerTest {",
              "     }",
              " ",
              "     @Test",
              "     public void testPropertiesAppIdHeader() throws IOException {",
              "         RabbitMQProducer producer = new RabbitMQProducer(endpoint);",
              "         message.setHeader(RabbitMQConstants.APP_ID, \"qweeqwe\");",
              "         AMQP.BasicProperties props = producer.buildProperties(exchange).build();",
              "         assertEquals(\"qweeqwe\", props.getAppId());",
              "     }",
              " ",
              "+    @Test",
              "+    public void testPropertiesOverrideNameHeader() throws IOException {",
              "+        RabbitMQProducer producer = new RabbitMQProducer(endpoint);",
              "+        message.setHeader(RabbitMQConstants.EXCHANGE_OVERRIDE_NAME, \"qweeqwe\");",
              "+        AMQP.BasicProperties props = producer.buildProperties(exchange).build();",
              "+        assertNull(props.getHeaders().get(RabbitMQConstants.EXCHANGE_OVERRIDE_NAME));",
              "+    }",
              "+",
              ""
            ]
    file_diff = FileDiff('Test', 'M', input)

    def testTokenizeLine(self):
        for l in self.input:
            print(tokenize_line(l))

    def testFileDiffDeleteUselessGitDiffOutput(self):
        self.file_diff.delete_useless_git_diff_output()

        self.assertNotIn('diff --git a/b5cb9bb9bf246fbd3f6bc957b5a538ea97de15ef '
                         'b/6f2f19b981c9fbc66138807b4d199851a2fd13e9',
                         self.file_diff.diff_body)
        self.assertNotIn('index b5cb9bb9bf2..6f2f19b981c 100644',
                         self.file_diff.diff_body)
        self.assertNotIn('--- a/b5cb9bb9bf246fbd3f6bc957b5a538ea97de15ef',
                         self.file_diff.diff_body)
        self.assertNotIn('+++ b/6f2f19b981c9fbc66138807b4d199851a2fd13e9',
                         self.file_diff.diff_body)

    def testFileDiffKeepOnlyNeededContextAroundChanges(self):
        self.file_diff.delete_useless_git_diff_output()
        self.file_diff.keep_only_needed_number_of_line_around_changes(1)

        self.assertIn('@@ -143,20 +143,28 @@ public class RabbitMQProducerTest {',
                      self.file_diff.diff_body)
        self.assertIn(' ',
                      self.file_diff.diff_body)
        self.assertIn('+    @Test',
                      self.file_diff.diff_body)
        self.assertIn('+    public void testPropertiesOverrideNameHeader() throws IOException {',
                      self.file_diff.diff_body)
        self.assertIn('+        RabbitMQProducer producer = new RabbitMQProducer(endpoint);',
                      self.file_diff.diff_body)
        self.assertIn('+        message.setHeader(RabbitMQConstants.EXCHANGE_OVERRIDE_NAME, \"qweeqwe\");',
                      self.file_diff.diff_body)
        self.assertIn('+        AMQP.BasicProperties props = producer.buildProperties(exchange).build();',
                      self.file_diff.diff_body)
        self.assertIn('+        assertNull(props.getHeaders().get(RabbitMQConstants.EXCHANGE_OVERRIDE_NAME));',
                      self.file_diff.diff_body)
        self.assertIn('+    }',
                      self.file_diff.diff_body)
        self.assertIn('+',
                      self.file_diff.diff_body)
        self.assertIn('',
                      self.file_diff.diff_body)

        self.assertNotIn('     @Test',
                         self.file_diff.diff_body)
        self.assertNotIn('     public void testPropertiesAppIdHeader() throws IOException {',
                         self.file_diff.diff_body)
        self.assertNotIn('         RabbitMQProducer producer = new RabbitMQProducer(endpoint);',
                         self.file_diff.diff_body)
        self.assertNotIn('         message.setHeader(RabbitMQConstants.APP_ID, \"qweeqwe\");',
                         self.file_diff.diff_body)
        self.assertNotIn('         AMQP.BasicProperties props = producer.buildProperties(exchange).build();',
                         self.file_diff.diff_body)
        self.assertNotIn('         assertEquals(\"qweeqwe\", props.getAppId());',
                         self.file_diff.diff_body)
        self.assertNotIn('     }',
                         self.file_diff.diff_body)

    def testFileDiffTokenizeEachLine(self):
        simple_diff_body: List[str] = [
            "     @Test",
            "     public void testPropertiesAppIdHeader() throws IOException {",
            "         RabbitMQProducer producer = new RabbitMQProducer(100);",
            "         message.setHeader(RabbitMQConstants.APP_ID, 100500);",
            "         AMQP.BasicProperties props = producer.buildProperties(exchange).build();",
            "         assertEquals(\"qweeqwe\", props.getAppId());",
            "     }",
        ]
        self.file_diff.diff_body = simple_diff_body
        print(self.file_diff.tokenize_each_line_of_diff_body())
        print(*self.file_diff.diff_body, sep='\n')

    def testFileDiffCamelCase(self):
        simple_diff_body: List[str] = [
            "     @Test",
            "     public void testPropertiesAppIdHeader() throws IOException {",
            "         RabbitMQProducer producer = new RabbitMQProducer(100);",
            "         AMQP.BasicProperties props = producer.buildProperties(exchange).build();",
            "         assertEquals(\"qweeqwe\", props.getAppId());",
            "     }",
        ]

        self.file_diff.diff_body = simple_diff_body
        self.file_diff.tokenize_each_line_of_diff_body()
        self.file_diff.tokenize_camel_case()
        print(*self.file_diff.diff_body, sep='\n')

    def testDiffBodyInOneLine(self):
        simple_diff_body: List[str] = [
            "     @Test",
            "     public void testPropertiesAppIdHeader() throws IOException {",
            "         RabbitMQProducer producer = new RabbitMQProducer(100);",
            "         AMQP.BasicProperties props = producer.buildProperties(exchange).build();",
            "         assertEquals(\"qweeqwe\", props.getAppId());",
            "     }",
        ]

        self.file_diff.diff_body = simple_diff_body
        print(self.file_diff.diff_body_in_one_line())
