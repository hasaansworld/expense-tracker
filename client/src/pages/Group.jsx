import { useParams } from "react-router-dom";
import { useEffect, useState } from "react";
import Card from "../components/Card";
import HypermediaClient from "../hypermedia";
import HypermediaForm from "../components/HypermediaForm";

const client = new HypermediaClient();
export default function Group() {
  const { groupId } = useParams();
  const [group, setGroup] = useState({});
  const [members, setMembers] = useState([]);
  const [memberActions, setMemberActions] = useState([]);
  const [expenses, setExpenses] = useState([]);
  const [expenseActions, setExpenseActions] = useState([]);
  const [settledMembers, setSettledMembers] = useState([]);
  const [showDialog, setShowDialog] = useState(false);
  const [dialogError, setDialogError] = useState("");

  const getActions = (response, setActions) => {
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
  };

  const processExpenseData = (expensesResponse, members) => {
    // Create a map of user_id to user_name for quick lookup
    const memberMap = {};
    members.forEach((member) => {
      memberMap[member.user_id] = member.user_name;
    });

    console.log("Expenses Response:", expensesResponse);
    // Process each expense
    return expensesResponse.expenses.map((expense) => {
      // Find the payer (participant with paid=1)
      const payer = expense.participants.find((p) => p.paid === 1);
      const payerId = payer ? payer.user_id : null;

      // Process participants with balance information
      const processedParticipants = expense.participants.map((participant) => {
        const isPayer = participant.user_id === payerId;
        const name = memberMap[participant.user_id] || "Unknown User";

        // Calculate balance
        // If you paid, you're owed the shares of all others except your own share
        // If you didn't pay, you owe your share
        let balance = 0;
        if (isPayer) {
          // Payer is owed all shares except their own
          const totalAmount = parseFloat(expense.amount);
          const ownShare = parseFloat(participant.share);
          balance = totalAmount - ownShare;
        } else {
          // Non-payer owes their share
          balance = -parseFloat(participant.share);
        }

        return {
          userId: participant.user_id,
          name,
          share: parseFloat(participant.share),
          paid: participant.paid === 1,
          isPayer,
          balance, // Positive if owed, negative if owe
        };
      });

      console.log("Processed Participants:", processedParticipants);

      // Return the processed expense
      return {
        id: expense.id,
        description: expense.description,
        amount: parseFloat(expense.amount),
        createdAt: expense.created_at,
        payerId,
        payerName: payerId ? memberMap[payerId] : "Unknown",
        participants: processedParticipants,
      };
    });
  };

  // Calculate the minimum number of payments to settle the group
  const calculateMinimumPayments = (expenses, members) => {
    // Initialize net balances for each member
    const balances = {};
    members.forEach((member) => {
      balances[member.user_id] = {
        user_id: member.user_id,
        user_name: member.user_name,
        balance: 0,
        owe: [],
        owed: [],
      };
    });

    // Calculate net balance for each person from all expenses
    expenses.forEach((expense) => {
      expense.participants.forEach((participant) => {
        balances[participant.userId].balance += participant.balance;
      });
    });

    // Separate members into those who owe money and those who are owed
    const debtors = Object.values(balances)
      .filter((member) => member.balance < 0)
      .sort((a, b) => a.balance - b.balance); // Sort by amount owed (ascending)

    const creditors = Object.values(balances)
      .filter((member) => member.balance > 0)
      .sort((a, b) => b.balance - a.balance); // Sort by amount owed (descending)

    // For each debtor, find creditors to pay to minimize transactions
    while (debtors.length > 0 && creditors.length > 0) {
      const debtor = debtors[0];
      const creditor = creditors[0];

      // Amount to transfer is the minimum of what debtor owes and what creditor is owed
      const amount = Math.min(Math.abs(debtor.balance), creditor.balance);

      // Round to 2 decimal places
      const roundedAmount = Math.round(amount * 100) / 100;

      if (roundedAmount >= 0.01) {
        // Only process transactions of at least 1 cent
        // Record the transaction
        debtor.owe.push(`${creditor.user_name} ${roundedAmount.toFixed(2)}`);
        creditor.owed.push(
          `${roundedAmount.toFixed(2)} by ${debtor.user_name}`
        );

        // Update balances
        debtor.balance += roundedAmount;
        creditor.balance -= roundedAmount;
      }

      // Remove members who are settled
      if (Math.abs(debtor.balance) < 0.01) {
        debtors.shift();
      }

      if (Math.abs(creditor.balance) < 0.01) {
        creditors.shift();
      }
    }

    return balances;
  };

  const deleteGroup = async () => {
    try {
      await client.navigateToRoot();
      await client.executeResourceOperation("Group", "DELETE", {
        group_id: groupId,
      });
      window.location.href = "/";
    } catch (error) {
      console.error("Error deleting group:", error);
      setDialogError(error.message);
    }
  };

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
      setGroup(groupResponse);
      await client.navigateToRoot();
      const groupMembersResponse = client.getResourceEndpoint(
        "Group Member",
        "GET"
      );
      const groupMembers = await client.navigateToUrl(
        groupMembersResponse.replace("<group_id>", groupId),
        "GET"
      );
      console.log("Group Members Response:", groupMembers);
      setMembers(groupMembers.members);
      getActions(groupMembers, setMemberActions);

      await client.navigateToRoot();
      const expensesResponse = await client.navigateToResource(
        "Expense",
        "GET",
        {
          group_id: groupId,
        }
      );

      const processedExpenses = processExpenseData(
        expensesResponse,
        groupMembers.members
      );
      setExpenses(processedExpenses);

      // Calculate minimum payments and update members with owe/owed information
      const settledMembers = calculateMinimumPayments(
        processedExpenses,
        groupMembers.members
      );
      setSettledMembers(settledMembers);

      getActions(expensesResponse, setExpenseActions);
    }
    if (groupId) navigateHypermedia();
  }, [groupId]);

  const colors = [
    "bg-red-500",
    "bg-blue-500",
    "bg-green-500",
    "bg-yellow-500",
    "bg-purple-500",
  ];
  const randomColor = colors[Math.floor(Math.random() * colors.length)];

  return (
    <div className="px-40 py-20 w-full h-full grid grid-cols-2 gap-32">
      <div className="w-full flex flex-col items-start">
        <div className="flex items-center gap-8">
          <p
            alt=""
            className={`w-16 h-16 flex text-white font-medium text-4xl items-center justify-center ${randomColor} rounded`}
          >
            {group.name ? group.name[0].toUpperCase() : ""}
          </p>
          <h1 className="text-3xl font-medium capitalize">{group.name}</h1>
        </div>

        <h1 className="text-lg font-semibold text-slate-500 mt-8">Expenses</h1>
        <div className="flex items-center gap-8 mb-8">
          {expenseActions.map((action) => (
            <a
              key={action.name}
              className="bg-gradient-to-r from-blue-500 to-purple-600 font-medium capitalize text-white px-4 py-1 rounded-md my-2"
              href={`${window.location.pathname}/${action.name}-expense`}
            >
              {action.name} Expense
            </a>
          ))}
        </div>
        {expenses.length === 0 && (
          <p className="text-gray-400 py-5">
            No expenses found. Expenses will show up here.
          </p>
        )}
        <div className="space-y-4 w-full">
          {expenses.map((expense) => (
            <div
              key={expense.id}
              className="w-full bg-white border-t border-gray-100 py-2"
            >
              {/* Expense header */}
              <div>
                <div className="flex justify-between items-center">
                  <h3 className="text-xl font-medium capitalize">
                    {expense.description}
                  </h3>
                  <span className="text-lg font-medium">
                    €{expense.amount.toFixed(2)}
                  </span>
                </div>
              </div>

              {/* Participants list with simplified one-line format */}
              <ul>
                {expense.participants.map((participant) => (
                  <li key={participant.userId} className="flex items-center">
                    <div
                      className={`font-medium ${
                        participant.balance > 0
                          ? "text-green-500"
                          : participant.balance < 0
                          ? "text-orange-500"
                          : "text-gray-600"
                      }`}
                    >
                      {participant.paid ? (
                        // Participant paid and is owed money
                        <span>
                          {participant.name} paid and is owed €
                          {participant.balance.toFixed(2)}
                        </span>
                      ) : (
                        // Participant owes money
                        <span>
                          {participant.name} owes €
                          {Math.abs(participant.balance).toFixed(2)}
                        </span>
                      )}

                      {/* For a fully settled participant (rare case) */}
                      {participant.balance === 0 && !participant.paid && (
                        <span>{participant.name} is settled (no balance)</span>
                      )}
                    </div>
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>
      </div>
      <div className="w-full flex flex-col items-start">
        <h1 className="text-lg text-slate-500 font-semibold px-2">
          Group Members
        </h1>
        <div className="flex items-center gap-8 mb-4">
          {memberActions.map((action) => (
            <a
              key={action.name}
              className="bg-gradient-to-r from-blue-500 to-purple-600 font-medium capitalize text-white px-4 py-1 rounded-md m-2"
              href={`${window.location.pathname}/${action.name}-members`}
            >
              {action.name} Member
            </a>
          ))}
        </div>
        {members.map((member) => {
          const settled = settledMembers[member.user_id];
          return (
            <div
              className="w-2/3 border-t border-gray-100 text-start"
              key={member.user_id}
            >
              <div className="w-full p-3 flex flex-col">
                <div className="flex items-center gap-4">
                  <p className="font-medium text-xl">{member.user_name}</p>
                  {member.role === "admin" && (
                    <p className="text-sm text-green-500 font-medium bg-green-100 px-2 rounded-lg">
                      Admin
                    </p>
                  )}
                </div>

                {/* Settlement information */}
                {settled && (
                  <div>
                    {settled.owe.length === 0 && settled.owed.length === 0 ? (
                      <p className="text-gray-400 font-medium">
                        All settled up
                      </p>
                    ) : (
                      <>
                        {settled.owe.map((owe, index) => (
                          <p
                            key={`owe-${index}`}
                            className="text-orange-500 font-medium"
                          >
                            owes {owe}
                          </p>
                        ))}
                        {settled.owed.map((owed, index) => (
                          <p
                            key={`owed-${index}`}
                            className="text-green-500 font-medium"
                          >
                            is owed {owed}
                          </p>
                        ))}
                      </>
                    )}
                  </div>
                )}
              </div>
            </div>
          );
        })}
        <button
          onClick={() => {
            setShowDialog(true);
            setDialogError("");
          }}
          className="mt-6 ml-2 px-3 py-1 rounded border border-red-200 hover:bg-red-100 text-red-500 font-medium transition-colors cursor-pointer"
        >
          Delete Group
        </button>
      </div>

      {showDialog && (
        <div
          onClick={() => setShowDialog(false)}
          className="w-screen h-screen absolute top-0 left-0 z-50 bg-gray-700/50"
        >
          <div className="flex flex-col w-full h-full items-center justify-center">
            <Card className="w-[400px] bg-white mx-auto">
              <h2 className="text-2xl font-semibold">Delete Group</h2>
              <p className="mt-2 text-gray-500">
                Are you sure you want to delete this group? This action cannot
                be undone.
              </p>
              <div className="flex gap-2 justify-end mt-6">
                <button
                  onClick={() => setShowDialog(false)}
                  className="flex-1 px-3 py-1.5 bg-gray-500 hover:bg-gray-600 text-white rounded cursor-pointer font-medium"
                >
                  Cancel
                </button>
                <button
                  onClick={deleteGroup}
                  className="flex-1 cursor-pointer px-3 py-1.5 font-medium bg-gradient-to-r from-red-500 to-red-600 text-white rounded hover:bg-red-600 focus:outline-none focus:ring-2 focus:ring-red-500 focus:ring-offset-2"
                >
                  Delete Group
                </button>
              </div>
              {dialogError && (
                <div className="text-red-500 mt-4">{dialogError}</div>
              )}
            </Card>
          </div>
        </div>
      )}
    </div>
  );
}
