import Header from "./header";
import ProtectedRoute from "./ProtectedRoute";

// Layout component that includes Header and handles protection
export default function RootLayout({ children, requireAuth = true }) {
  if (requireAuth) {
    return (
      <>
        <Header />
        <ProtectedRoute>{children}</ProtectedRoute>
      </>
    );
  }

  return (
    <>
      <Header />
      {children}
    </>
  );
}
