import { createBrowserRouter, RouterProvider } from "react-router-dom";
import { useEffect, useState } from "react";
import RootLayout from "./components/RootLayout";
import Signup from "./pages/Signup";
import "./App.css";
import Home from "./pages/Home";
import CreateGroup from "./pages/CreateGroup";
import Group from "./pages/Group";

const router = createBrowserRouter([
  {
    path: "/",
    element: (
      <RootLayout>
        <Home />
      </RootLayout>
    ),
  },
  {
    path: "/signup",
    element: (
      <RootLayout requireAuth={false}>
        <Signup />
      </RootLayout>
    ),
  },
  {
    path: "/groups/create",
    element: (
      <RootLayout requireAuth={false}>
        <CreateGroup />
      </RootLayout>
    ),
  },
  {
    path: "/groups/:groupId",
    element: (
      <RootLayout requireAuth={false}>
        <Group />
      </RootLayout>
    ),
  },
  // All other routes will be protected by default
  // Example of another protected route:
  // {
  //   path: "/dashboard",
  //   element: (
  //     <RootLayout>
  //       <Dashboard />
  //     </RootLayout>
  //   ),
  // },
]);

export default function App() {
  const [isReady, setIsReady] = useState(false);

  useEffect(() => {
    // This ensures hydration happens after we can access localStorage
    setIsReady(true);
  }, []);

  if (!isReady) {
    return null; // Or a loading spinner
  }

  return (
    <div className="w-screen h-screen overflow-y-auto box-border">
      <RouterProvider router={router} />
    </div>
  );
}
