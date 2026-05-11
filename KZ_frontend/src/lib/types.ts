/**
 * Knowledge Zakat — Central TypeScript types.
 *
 * Every API entity has a single canonical type definition here. Pages
 * import these types instead of redeclaring shapes inline. This way,
 * if the backend renames a field (say, `firstname` -> `first_name`),
 * the compiler points us at every site that needs updating, instead
 * of letting bugs slip through at runtime.
 *
 * Naming convention:
 *   - `*Response`  matches the JSON shape the API returns.
 *   - `*Input`     matches the body we send in POST/PUT requests.
 *   - Domain types (User, Session, ...) are aliased to their Response
 *     forms for readability inside components.
 */

// ---------------------------------------------------------------------------
// Roles & Users
// ---------------------------------------------------------------------------

export type RoleName = 'student' | 'teacher' | 'admin';

export interface Role {
  id: number;
  role_name: RoleName;
}

export interface User {
  id: number;
  firstname: string;
  lastname: string;
  email: string;
  is_active: boolean;
  bio: string | null;
  roles: Role[];
  /** Data URL (data:image/...;base64,...) or null. The backend already
   *  encodes the BLOB before sending. */
  profile_image: string | null;
}

// ---------------------------------------------------------------------------
// Categories & Sessions
// ---------------------------------------------------------------------------

export interface Category {
  id: number;
  category_name: string;
}

export interface Session {
  id: number;
  title: string;
  description: string | null;
  session_duration: number;
  /** ISO-8601 timestamp string. Convert to Date only at display time. */
  date_time: string;
  meeting_link: string | null;
  cover_image_url: string | null;
  categories: Category[];
  teacher_id: number | null;
  teacher_name: string | null;
  display_cover: string | null;
}

// ---------------------------------------------------------------------------
// Enrollments
// ---------------------------------------------------------------------------

export type EnrollmentStatus = 'pending' | 'approved' | 'rejected';

export interface MyEnrollment {
  session_id: number;
  session_title: string;
  lecture_title: string;
  teacher_name: string;
  date: string;
  time: string;
  day: string;
  duration: number;
  status: EnrollmentStatus;
  meeting_link: string | null;
}

// ---------------------------------------------------------------------------
// Auth
// ---------------------------------------------------------------------------

export interface LoginInput {
  email: string;
  password: string;
}

export interface TokenResponse {
  access_token: string;
  token_type: 'bearer';
}

// ---------------------------------------------------------------------------
// Notifications
// ---------------------------------------------------------------------------

export type NotificationKind = 'success' | 'error' | 'info' | 'warning';

export interface AppNotification {
  id: number;
  kind: NotificationKind;
  message: string;
  /** Auto-dismiss after this many ms. 0 means stays until dismissed. */
  duration: number;
}

// ---------------------------------------------------------------------------
// Routing
// ---------------------------------------------------------------------------
//
// A route is encoded into the URL hash as `#/<name>` or
// `#/<name>/<param>`. Pages that need a payload pull it from
// `route.params` rather than from a shared store, which keeps each
// page self-contained.

/** All page identifiers known to the router. Adding a new page is a
 *  one-line edit here, plus a case in App.svelte. */
export type RouteName =
  // Public
  | 'login'
  | 'register'
  // Student
  | 'home'
  | 'my_learning'
  | 'student_profile'
  | 'session_view'
  | 'session_details'
  | 'teacher_view'
  // Teacher
  | 'teacher_home'
  | 'create_session'
  | 'my_lectures'
  | 'teacher_requests'
  | 'profile'
  | 'update_session'
  // Admin
  | 'admin_logs'
  | 'admin_dashboard'
  | 'admin_panel';

export interface Route {
  name: RouteName;
  /** Optional positional param parsed from the URL (e.g. `#/teacher_view/5` -> '5'). */
  param: string | null;
}
