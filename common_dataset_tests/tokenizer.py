import unittest

from NMT.students.logs.tokenizer import tokenize_line


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

    def testTokenizeLine(self):
        for l in self.input:
            print(tokenize_line(l))

