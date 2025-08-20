# FreeNet 🌐

**FreeNet** is an open-source experimental browser that uses [Reticulum](https://github.com/markqvist/Reticulum) to explore and participate in a **free, decentralized internet**.  
It aims to give users a censorship-resistant, peer-to-peer alternative to the traditional web, where everyone can host, share, and access information without relying on centralized servers.

FreeNet is still in active development — the repository currently provides **Windows** and **macOS** builds, with the full source code coming soon.

---

## 🔥 Key Features

- **Mussoulini Search** - Your Search engine, other freeNet's pages will appear here!
- **Decentralized Networking** – Built on Reticulum, a resilient peer-to-peer communication stack.  
- **Cross-Platform** – Runs on both Windows and macOS (Linux support planned).  
- **Open Source** – Transparent, community-driven development.  
- **Freedom-Oriented** – No central authorities, no gatekeepers, no dependencies on corporate infrastructure.  
- **Custom Content Hosting** – Add your own `index.html` to your system’s `AppData` (Windows) or `Application Support` (macOS) to host and share with others directly through FreeNet.  
- **Lightweight & Minimalist** – Designed to be fast, simple, and accessible to everyone.

---

## 🌍 Why FreeNet?

The modern internet is increasingly centralized, censored, and controlled by large corporations and governments.  
FreeNet is a step toward reclaiming digital independence by enabling a truly free network where:

- Anyone can publish content without permission.  
- Communities can connect without surveillance or gatekeeping.  
- Access is resilient, even in restrictive environments.  

---

## 🚧 Roadmap

- [x] Source code release  (Give me some time to clean this before releasing under my name :P )
- [ ] Linux support  
- [ ] Improved UI/UX  
- [ ] Plugins/extensions for richer decentralized apps  

---

## ⚡ Get Started

1. Download the latest **Windows** or **macOS** release from the [Releases](./releases) page.  
2. Launch FreeNet and start exploring the free internet through Reticulum.  
3. Share your own content by placing `index.html` in the appropriate folder:  
   - **Windows** → `%AppData%\FreeNet\config\serverPages`  
   - **macOS** → `~/Library/Application Support/FreeNet/config/serverPages`
   - **Warning** → Please remember to use `freenet://` to your page, or just add nothing that the app will deal with it for you! Otherwise you will be redirecting to the "conventional" internet!
4. In MacOs you will need to give the app an exception to Gatekeeper with `xattr -cr **ApplicationPath**`

---

## 🤝 Contributing

We welcome contributions of all kinds — from code and documentation to ideas and testing.  
The goal is to build FreeNet together, as a community-driven effort to preserve online freedom.  

---

## 📜 License

FreeNet is released under the [MIT License](./LICENSE), ensuring that it will always remain free and open for everyone.  
