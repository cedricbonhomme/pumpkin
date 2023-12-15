import asyncio
import base64

import rfc3161ng
import spade
from spade.agent import Agent
from spade.behaviour import CyclicBehaviour
from spade.behaviour import OneShotBehaviour
from spade.message import Message

# import getpass

try:
    from instance import config
except Exception:
    from instance import example as config


CERTIFICATE = open(config.CERTIFICATE_FILE, "rb").read()
RT = rfc3161ng.RemoteTimestamper(config.REMOTE_TIMESTAMPER, certificate=CERTIFICATE)


class AggregationEngine(Agent):
    class CollectingBehav(CyclicBehaviour):
        async def on_start(self):
            print("Starting behaviour...")
            # self.counter = 0

        async def run(self):
            # print(f"Counter: {self.counter}")
            # self.counter += 1

            msg = await self.receive(timeout=10)  # wait for a message for 10 seconds
            if msg:
                print(f"Message received with content: {msg.body}")
                print(base64.b64decode(msg.body))
                # m = hashlib.sha256()
                # m.update(result)
                # base64_result = m.hexdigest()
                tst = RT.timestamp(data=msg.body)
                # TODO: validate the format with pydantic before storing in database
                item = {
                    "tst": tst,
                    "scan_result": msg.body,
                }
                print(item)
                print()
            else:
                print("Did not received any message after 10 seconds")

    class SharingBehav(OneShotBehaviour):
        async def run(self):
            print("SharingBehav running")
            msg = Message(to="probe1@localhost")  # Instantiate the message
            msg.set_metadata(
                "performative", "inform"
            )  # Set the "inform" FIPA performative
            msg.set_metadata(
                "ontology", "myOntology"
            )  # Set the ontology of the message content
            msg.set_metadata(
                "language", "OWL-S"
            )  # Set the language of the message content
            msg.body = "data"  # Set the message content

            await self.send(msg)
            print("Message sent!")

            # set exit_code for the behaviour
            self.exit_code = "Job Finished!"

            # stop agent from behaviour
            # await self.agent.stop()

    async def setup(self):
        print("Agent starting . . .")
        collecting_behav = self.CollectingBehav()
        self.add_behaviour(collecting_behav)

        # self.sharing_behav = self.SharingBehav()
        # self.add_behaviour(self.sharing_behav)

        self.presence.set_available()
        self.presence.subscribe("probe1@localhost")


async def main():
    # do not forget to configure OMEMO
    jid = "correlation-engine@localhost"
    passwd = "securePasswordforCE"  # getpass.getpass(f"Password for {jid}:\n")
    agent = AggregationEngine(jid, passwd)
    await agent.start()

    await agent.web.start(hostname="127.0.0.1", port="10000")
    print("Web Graphical Interface available at:")
    print("http://127.0.0.1:10000/spade")
    print("Wait until user interrupts with ctrl+C")

    # wait until user interrupts with ctrl+C
    while True:  # not agent.CollectingBehav.is_killed():
        try:
            await asyncio.sleep(1)
        except KeyboardInterrupt:
            break

    assert agent.CollectingBehav.exit_code == 10

    await agent.stop()


if __name__ == "__main__":
    spade.run(main())