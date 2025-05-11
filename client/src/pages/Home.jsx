import HypermediaClient from "../hypermedia";
import { useEffect, useState } from "react";

const client = new HypermediaClient();

export default function Home() {
  const [groups, setGroups] = useState([]);
  useEffect(() => {
    async function navigateHypermedia() {
      // Initialize and load routes
      await client.navigateToRoot();
      const response = await client.navigateToResource("Group", "GET");
      if (response) {
        setGroups(response.groups);
      }
      console.log("response", response);
    }
    navigateHypermedia();
  }, []);
  return (
    <div className="pt-30 px-16 flex flex-col items-center">
      <h1 className="text-2xl font-medium">Groups</h1>
    </div>
  );
}
