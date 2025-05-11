import HypermediaClient from "../hypermedia";
import { useEffect, useState } from "react";

const client = new HypermediaClient();

export default function Home() {
  const [groups, setGroups] = useState([]);
  const [actions, setActions] = useState([]);

  useEffect(() => {
    async function navigateHypermedia() {
      // Initialize and load routes
      await client.navigateToRoot();
      const response = await client.navigateToResource("Group", "GET");
      if (response) {
        setGroups(response.groups);
      }
      const ctrls = [];

      // Loop through all controls
      for (const [controlName, controlValue] of Object.entries(
        response["@controls"]
      )) {
        // Skip the 'self' control
        if (controlName !== "self") {
          // Add control name to the control object
          ctrls.push({
            name: controlName,
            ...controlValue,
          });
        }
      }
      setActions(ctrls);
      console.log("response", response);
    }
    navigateHypermedia();
  }, []);
  return (
    <div className="pt-30 px-16 flex flex-col items-center">
      {actions.map((action) => (
        <a
          key={action.name}
          className="bg-gradient-to-r from-blue-500 to-purple-600 font-bold capitalize text-white px-4 py-2 rounded-md m-2"
          href={`/groups/${action.name}`}
        >
          {action.name} Group
        </a>
      ))}
      {groups.length === 0 && (
        <p className="text-lg text-gray-400 p-5">
          No groups found. Groups will show up here.
        </p>
      )}
    </div>
  );
}
