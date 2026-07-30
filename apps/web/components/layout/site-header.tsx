"use client";

import {
  BookOpen,
  ChevronDown,
  GraduationCap,
  LayoutDashboard,
  LogOut,
  Menu,
  Search,
  Settings,
  ShieldCheck,
  ShoppingCart,
  User as UserIcon,
  X,
} from "lucide-react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import * as React from "react";

import { Avatar } from "@/components/ui/misc";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { useAuth } from "@/lib/hooks/use-auth";
import { useCart } from "@/lib/hooks/use-cart";
import { ROLE_LABELS, cn } from "@/lib/utils";

const NAV_LINKS = [
  { href: "/courses", label: "Kurslar" },
  { href: "/teach", label: "Ustozlar uchun" },
  { href: "/business", label: "Biznes uchun" },
  { href: "/pricing", label: "Narxlar" },
];

export function SiteHeader() {
  const { user, logout } = useAuth();
  const { count } = useCart();
  const router = useRouter();

  const [mobileOpen, setMobileOpen] = React.useState(false);
  const [menuOpen, setMenuOpen] = React.useState(false);
  const [search, setSearch] = React.useState("");
  const menuRef = React.useRef<HTMLDivElement>(null);

  React.useEffect(() => {
    const handler = (event: MouseEvent) => {
      if (menuRef.current && !menuRef.current.contains(event.target as Node)) {
        setMenuOpen(false);
      }
    };
    document.addEventListener("mousedown", handler);
    return () => document.removeEventListener("mousedown", handler);
  }, []);

  const submitSearch = (event: React.FormEvent) => {
    event.preventDefault();
    const query = search.trim();
    router.push(query ? `/courses?search=${encodeURIComponent(query)}` : "/courses");
    setMobileOpen(false);
  };

  const dashboardHref =
    user?.role === "admin"
      ? "/super-admin"
      : user?.role === "teacher" || user?.role === "org_admin"
        ? "/teacher/courses"
        : user?.role === "b2b_manager"
          ? "/b2b/dashboard"
          : "/dashboard";

  return (
    <header className="sticky top-0 z-40 w-full border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/80">
      <div className="container-page flex h-16 items-center gap-3">
        {/* Logo */}
        <Link href="/" className="flex shrink-0 items-center gap-2" aria-label="Zehno.uz bosh sahifa">
          <span className="flex size-9 items-center justify-center rounded-lg bg-primary text-primary-foreground">
            <GraduationCap className="size-5" />
          </span>
          <span className="text-lg font-bold tracking-tight">
            Zehno<span className="text-primary">.uz</span>
          </span>
        </Link>

        {/* Desktop navigatsiya */}
        <nav className="ml-4 hidden items-center gap-1 lg:flex">
          {NAV_LINKS.map((link) => (
            <Link
              key={link.href}
              href={link.href}
              className="rounded-lg px-3 py-2 text-sm font-medium text-muted-foreground transition-colors hover:bg-muted hover:text-foreground"
            >
              {link.label}
            </Link>
          ))}
        </nav>

        {/* Qidiruv */}
        <form onSubmit={submitSearch} className="ml-auto hidden max-w-sm flex-1 md:block">
          <div className="relative">
            <Search
              className="pointer-events-none absolute left-3 top-1/2 size-4 -translate-y-1/2 text-muted-foreground"
              aria-hidden
            />
            <Input
              value={search}
              onChange={(event) => setSearch(event.target.value)}
              placeholder="Kurs qidirish..."
              className="pl-9"
              aria-label="Kurs qidirish"
            />
          </div>
        </form>

        {/* O'ng tomon */}
        <div className="ml-auto flex items-center gap-1.5 md:ml-3">
          <Link
            href="/cart"
            className="relative rounded-lg p-2.5 text-muted-foreground hover:bg-muted hover:text-foreground"
            aria-label={`Savat (${count})`}
          >
            <ShoppingCart className="size-5" />
            {count > 0 ? (
              <span className="absolute -right-0.5 -top-0.5 flex size-5 items-center justify-center rounded-full bg-primary text-2xs font-bold text-primary-foreground">
                {count}
              </span>
            ) : null}
          </Link>

          {user ? (
            <div className="relative" ref={menuRef}>
              <button
                type="button"
                onClick={() => setMenuOpen((prev) => !prev)}
                aria-expanded={menuOpen}
                aria-haspopup="menu"
                className="flex items-center gap-2 rounded-lg p-1 pr-2 hover:bg-muted"
              >
                <Avatar name={user.full_name} src={user.avatar_url} size={32} />
                <ChevronDown className="size-4 text-muted-foreground" aria-hidden />
              </button>

              {menuOpen ? (
                <div
                  role="menu"
                  className="absolute right-0 top-full mt-2 w-60 animate-fade-in overflow-hidden rounded-xl border bg-popover p-1.5 shadow-card-hover"
                >
                  <div className="border-b px-3 pb-2.5 pt-2">
                    <p className="truncate text-sm font-semibold">{user.full_name}</p>
                    <p className="truncate text-xs text-muted-foreground">{user.email}</p>
                    <p className="mt-1 text-2xs font-medium uppercase tracking-wide text-primary">
                      {ROLE_LABELS[user.role]}
                    </p>
                  </div>

                  <MenuLink href={dashboardHref} icon={LayoutDashboard} onClick={() => setMenuOpen(false)}>
                    Boshqaruv paneli
                  </MenuLink>
                  <MenuLink href="/dashboard" icon={BookOpen} onClick={() => setMenuOpen(false)}>
                    Mening kurslarim
                  </MenuLink>
                  <MenuLink href="/profile" icon={UserIcon} onClick={() => setMenuOpen(false)}>
                    Profil
                  </MenuLink>
                  {user.role === "admin" ? (
                    <MenuLink href="/super-admin" icon={ShieldCheck} onClick={() => setMenuOpen(false)}>
                      Super-admin panel
                    </MenuLink>
                  ) : null}
                  <MenuLink href="/profile/settings" icon={Settings} onClick={() => setMenuOpen(false)}>
                    Sozlamalar
                  </MenuLink>

                  <button
                    type="button"
                    role="menuitem"
                    onClick={async () => {
                      setMenuOpen(false);
                      await logout();
                      router.push("/");
                    }}
                    className="flex w-full items-center gap-2.5 rounded-lg px-3 py-2 text-sm text-destructive hover:bg-destructive/10"
                  >
                    <LogOut className="size-4" />
                    Chiqish
                  </button>
                </div>
              ) : null}
            </div>
          ) : (
            <div className="hidden items-center gap-2 sm:flex">
              <Button variant="ghost" size="sm" onClick={() => router.push("/login")}>
                Kirish
              </Button>
              <Button size="sm" onClick={() => router.push("/register")}>
                Ro&apos;yxatdan o&apos;tish
              </Button>
            </div>
          )}

          <button
            type="button"
            onClick={() => setMobileOpen((prev) => !prev)}
            className="rounded-lg p-2.5 hover:bg-muted lg:hidden"
            aria-label="Menyu"
            aria-expanded={mobileOpen}
          >
            {mobileOpen ? <X className="size-5" /> : <Menu className="size-5" />}
          </button>
        </div>
      </div>

      {/* Mobil menyu */}
      {mobileOpen ? (
        <div className="animate-fade-in border-t bg-background lg:hidden">
          <div className="container-page space-y-1 py-3">
            <form onSubmit={submitSearch} className="mb-3 md:hidden">
              <div className="relative">
                <Search
                  className="pointer-events-none absolute left-3 top-1/2 size-4 -translate-y-1/2 text-muted-foreground"
                  aria-hidden
                />
                <Input
                  value={search}
                  onChange={(event) => setSearch(event.target.value)}
                  placeholder="Kurs qidirish..."
                  className="pl-9"
                />
              </div>
            </form>

            {NAV_LINKS.map((link) => (
              <Link
                key={link.href}
                href={link.href}
                onClick={() => setMobileOpen(false)}
                className="block rounded-lg px-3 py-2.5 text-sm font-medium hover:bg-muted"
              >
                {link.label}
              </Link>
            ))}

            {!user ? (
              <div className="flex gap-2 pt-2">
                <Button variant="outline" full onClick={() => router.push("/login")}>
                  Kirish
                </Button>
                <Button full onClick={() => router.push("/register")}>
                  Ro&apos;yxatdan o&apos;tish
                </Button>
              </div>
            ) : null}
          </div>
        </div>
      ) : null}
    </header>
  );
}

function MenuLink({
  href,
  icon: Icon,
  children,
  onClick,
  className,
}: {
  href: string;
  icon: React.ComponentType<{ className?: string }>;
  children: React.ReactNode;
  onClick?: () => void;
  className?: string;
}) {
  return (
    <Link
      href={href}
      role="menuitem"
      onClick={onClick}
      className={cn(
        "flex items-center gap-2.5 rounded-lg px-3 py-2 text-sm hover:bg-muted",
        className,
      )}
    >
      <Icon className="size-4 text-muted-foreground" />
      {children}
    </Link>
  );
}
