import {createApp} from "vue";
import ElementPlus from "element-plus";
import "element-plus/dist/index.css";
import "element-plus/theme-chalk/dark/css-vars.css";
import "highlight.js/styles/github.min.css";
import "./styles/theme/tokens.css";
import "./styles/transitions.css";
import "./styles/answer-prose.css";
import * as ElementPlusIconsVue from "@element-plus/icons-vue";
import {initTheme} from "./modules/theme";
import App from "./App.vue";

initTheme();

const app = createApp(App);
app.use(ElementPlus);
for (const [key, component] of Object.entries(ElementPlusIconsVue)) {
  app.component(key, component);
}
app.mount("#app");
