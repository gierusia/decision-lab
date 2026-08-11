export const metadata = {
  title: "Decision Lab",
  description: "Decision Lab — каркас (Этап 0)",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="ru">
      <body>{children}</body>
    </html>
  );
}
