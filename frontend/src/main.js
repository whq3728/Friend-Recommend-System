import { createApp } from "vue";
import { createPinia } from "pinia";
import App from "./App.vue";
import router from "./router";
import "./styles/global.css";

// 应用入口：注册状态管理与路由后挂载根组件
const app = createApp(App);
app.use(createPinia());
app.use(router);
app.mount("#app");
