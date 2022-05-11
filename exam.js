async function getData() {
    n=1
    try {
        m=n/0
        print(m)
    } catch(err) {
      throw err
    }
}
getData();