/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./app/templates/**/*.html",
    "./app/static/js/**/*.js",
  ],
  theme: {
    extend: {
      colors: {
        chocolate: {
          DEFAULT: "#412919",
          deep: "#412919",
          support: "#5A3B26",
        },
        gold: {
          DEFAULT: "#BE9D4F",
          antique: "#BE9D4F",
          soft: "#B99E5B",
        },
        cream: {
          DEFAULT: "#FAF8F4",
          page: "#FAF8F4",
          soft: "#F3EEE4",
          deep: "#EBE3D4",
        },
        ink: {
          DEFAULT: "#29231F",
          muted: "#746B63",
        },
      },
      fontFamily: {
        display: ['"Cormorant Garamond"', "Georgia", "serif"],
        sans: ['"Source Sans 3"', "system-ui", "sans-serif"],
      },
      boxShadow: {
        soft: "0 8px 30px rgba(65, 41, 25, 0.08)",
        card: "0 4px 20px rgba(65, 41, 25, 0.06)",
      },
      maxWidth: {
        content: "80rem",
      },
      height: {
        18: "4.5rem",
      },
    },
  },
  plugins: [
    require("@tailwindcss/forms"),
    require("@tailwindcss/typography"),
  ],
};
