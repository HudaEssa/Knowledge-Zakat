/**
 * Knowledge Zakat — Centralised Lucide icon imports.
 *
 * We re-export only the icons we actually use, which keeps the bundle
 * small (Lucide is tree-shakeable but importing from a single place
 * makes the icon set a controlled vocabulary rather than a free-for-all).
 *
 * Why a centralised file:
 *  1. One place to swap an icon (e.g. if `BookOpen` is used in 12 files
 *     and we want `GraduationCap` instead, change here only).
 *  2. New developers see the available icon set at a glance.
 *  3. Eliminates the temptation to import emojis as fallbacks.
 *
 * Usage in components:
 *   <script>
 *     import { BookOpen } from 'lucide-svelte';
 *   </script>
 *   <BookOpen size={20} class="text-brand" />
 *
 * Or via the <Icon> wrapper (lib/components/ui/Icon.svelte) for a
 * consistent default size and style:
 *   <Icon name="book-open" />
 */

export {
  // Navigation & layout
  Home,
  LayoutDashboard,
  Menu,
  X,
  ChevronRight,
  ChevronLeft,
  ChevronDown,
  ChevronUp,
  ArrowRight,
  ArrowLeft,
  MoreHorizontal,
  MoreVertical,
  Settings,
  LogOut,

  // Education & content
  BookOpen,
  GraduationCap,
  Library,
  FileText,
  Video,
  Mic,
  Calendar,
  Clock,
  CheckCircle2,
  Award,
  Star,

  // Users
  User,
  Users,
  UserPlus,
  UserCheck,
  UserX,
  ShieldCheck,
  Shield,

  // Actions
  Plus,
  Minus,
  Search,
  Filter,
  Edit,
  Edit2,
  Edit3,
  Trash2,
  Save,
  Upload,
  Download,
  Copy,
  Share2,
  ExternalLink,
  Link as LinkIcon,
  Eye,
  EyeOff,
  RefreshCw,

  // Status / feedback
  Check,
  CheckCheck,
  AlertCircle,
  AlertTriangle,
  Info,
  HelpCircle,
  Loader2,
  Sparkles,

  // Communication
  Mail,
  MessageCircle,
  MessageSquare,
  Bell,
  BellOff,
  Send,
  Phone,

  // Media
  Image,
  ImagePlus,
  Camera,
  Paperclip,
  PlayCircle,
  PauseCircle,

  // Misc
  Tag,
  Tags,
  Hash,
  Globe,
  Heart,
  Bookmark,
  Flag,
  ThumbsUp,
  ThumbsDown,
  Zap,
  TrendingUp,
  BarChart3,
  PieChart,
  Activity,
  Layers,
  Grid3x3,
  List,
  Lock,
  Unlock,
  KeyRound,
  Inbox,
} from 'lucide-svelte';
