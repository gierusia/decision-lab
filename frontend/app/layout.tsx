import "./globals.css";

export const metadata = {
  title: "Decision Lab",
  description: "Решения и эксперименты команды",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="ru">
      <body>{children}</body>
    </html>
  );
}
