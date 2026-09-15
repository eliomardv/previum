import { createRouter, createWebHashHistory } from 'vue-router'
import { useSession } from './stores/session'
import Login from './views/Login.vue'
import Dashboard from './views/Dashboard.vue'
import Records from './views/Records.vue'
export const router = createRouter({
  history: createWebHashHistory(),
  routes: [
    { path: '/login', component: Login },
    { path: '/', component: Dashboard },
    { path: '/companies', component: Records, props: { kind: 'companies' } },
    { path: '/workers', component: Records, props: { kind: 'workers' } },
    { path: '/:pathMatch(.*)*', redirect: '/' },
  ],
})
router.beforeEach(to => {
  const session = useSession()
  if (!session.token && to.path !== '/login') return '/login'
  if (session.token && to.path === '/login') return '/'
})
