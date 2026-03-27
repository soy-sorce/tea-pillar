// src/App.tsx
import { createBrowserRouter, RouterProvider } from "react-router-dom";
import { GenerationContextProvider } from "@/contexts/GenerationContext";
import { AppLayout } from "@/components/layout/AppLayout";
import { TopPage } from "@/pages/TopPage";
import { ResultPage } from "@/pages/ResultPage";

const router = createBrowserRouter([
  {
    path: "/",
    element: <AppLayout />,
    children: [
      { index: true, element: <TopPage /> },
      { path: "result", element: <ResultPage /> },
    ],
  },
]);

export function App(): React.JSX.Element {
  return (
    <GenerationContextProvider>
      <RouterProvider router={router} />
    </GenerationContextProvider>
  );
}
