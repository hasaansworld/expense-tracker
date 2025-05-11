import { useParams } from "react-router-dom";
import { useEffect, useState } from "react";
import Card from "../components/Card";
import HypermediaClient from "../hypermedia";
import HypermediaForm from "../components/HypermediaForm";

const client = new HypermediaClient();
export default function Group() {
  const { groupId } = useParams();
  const [group, setGroup] = useState({});

  useEffect(() => {
    async function navigateHypermedia() {
      // Initialize and load routes
      await client.navigateToRoot();
      const groupsResponse = await client.navigateToResource("Group", "GET");
      const url = groupsResponse["@controls"].self.href;
      const groupResponse = await client.navigateToUrl(
        `/api${url}${groupId}`,
        "GET"
      );
      console.log("Group Response:", groupResponse);
    }
    if (groupId) navigateHypermedia();
  }, [groupId]);

  return (
    <div className="p-20 w-full h-full flex flex-col items-center justify-center">
      <h1>Group</h1>
    </div>
  );
}
