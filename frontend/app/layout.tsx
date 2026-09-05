export const metadata = {
  title: "Decision Lab",
  description: "Решения и эксперименты команды",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="ru">
      <body
        style={{
          margin: 0,
          fontFamily: "ui-sans-serif, system-ui, sans-serif",
          background: "#f6f7f9",
          color: "#1b1f24",
        }}
      >
        {children}
      </body>
    </html>
  );
}
