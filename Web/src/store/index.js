import { createStore } from 'vuex'

const store = createStore({
  
  actions: {
    login({ commit }, userInfo) {
      commit('login', userInfo)
    },
    logout({ commit }) {
      commit('logout')
    }
  },
  getters: {
    isLoggedIn: state => state.isLoggedIn,
    userInfo: state => state.userInfo
  }
})

export default store
