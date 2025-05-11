import Card from "../components/Card";

export default function Signup() {
  return (
    <div className="p-20 w-full h-full flex flex-col items-center justify-center">
      <Card className="w-[400px]">
        <h1 className="text-2xl font-semibold">Signup</h1>
        <p className="mt-2 text-gray-500">Create an account to continue</p>
      </Card>
    </div>
  );
}
