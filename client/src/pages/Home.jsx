import Card from "../components/Card";
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
      setGroups(response.groups);
      console.log("response", response);
    }
    navigateHypermedia();
  }, []);

  const colors = [
    "bg-red-500",
    "bg-blue-500",
    "bg-green-500",
    "bg-yellow-500",
    "bg-purple-500",
  ];

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
      {groups.length > 0 && (
        <div className="w-2/3 grid grid-cols-3 gap-8 mt-10">
          {groups.map((group, index) => (
            <a className="flex" href={`/groups/${group.id}`} key={group.id}>
              <div
                key={group.id}
                className="bg-white hover:bg-gray-100 cursor-pointer border border-gray-200 rounded-lg flex items-center gap-8 !p-4 w-full max-w-md"
              >
                <p
                  alt=""
                  className={`w-16 h-16 flex text-white font-medium text-4xl items-center justify-center ${
                    colors[index % colors.length]
                  } rounded`}
                >
                  {group.name ? group.name[0].toUpperCase() : ""}
                </p>
                <h2 className="text-xl font-medium capitalize p-4">
                  {group.name}
                </h2>
                <p className="text-gray-500">{group.description}</p>
              </div>
            </a>
          ))}
        </div>
      )}
    </div>
  );
}
