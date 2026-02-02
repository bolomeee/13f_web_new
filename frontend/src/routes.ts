import { createBrowserRouter } from "react-router";
import { Root } from "./components/Root";
import { Dashboard } from "./components/Dashboard";
import { Settings } from "./components/Settings";
import { InstitutionDetail } from "./components/InstitutionDetail";

export const router = createBrowserRouter([
  {
    path: "/",
    Component: Root,
    children: [
      { index: true, Component: Dashboard },
      { path: "settings", Component: Settings },
      { path: "institution/:id", Component: InstitutionDetail },
    ],
  },
]);